import logging
from datetime import datetime
from typing import Dict, List, Optional, Set

from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.responses import JSONResponse

from app.core.content_utils import strip_markup
from app.core.emailer import send_email
from app.core.ingestion import ingest_feed
from app.core.llm_utils import (
    fallback_summary,
    normalize_summary,
    render_newsletter,
    summarize_story,
    summary_is_informative,
)
from app.core.schemas import PipelineRequest, SendRequest
from app.core.supabase_client import get_client

router = APIRouter()
logger = logging.getLogger(__name__)

TOP_STORY_LIMIT = 10


def _fetch_top_items(
    sb, limit: int = TOP_STORY_LIMIT, source_ids: Optional[List[int]] = None
) -> List[Dict]:
    query = sb.table("items").select("*")
    if source_ids:
        query = query.in_("source_id", source_ids)
    res = query.order("published", desc=True).limit(limit).execute()
    return res.data or []


def _ensure_story_format(item: Dict) -> Dict:
    fallback_title = item.get("title") or "Untitled"
    existing_summary = item.get("summary") or ""

    if existing_summary:
        normalized = normalize_summary(existing_summary)
        if summary_is_informative(normalized):
            item["summary"] = normalized
            item["title"] = fallback_title
            return item

    article_text = item.get("content") or existing_summary or fallback_title
    story = summarize_story(article_text, fallback_title)

    if not summary_is_informative(story["summary"]):
        alternate_source = " ".join(
            filter(
                None,
                [
                    fallback_title,
                    item.get("content"),
                    existing_summary,
                ],
            )
        )
        if alternate_source.strip():
            alternate_story = summarize_story(alternate_source, fallback_title)
            if summary_is_informative(alternate_story["summary"]):
                story = alternate_story

    if not summary_is_informative(story["summary"]):
        story["summary"] = fallback_summary(story["headline"])

    item["title"] = story["headline"]
    item["summary"] = normalize_summary(story["summary"])
    return item


def _build_newsletter(
    sb, source_ids: Optional[List[int]] = None, limit: int = TOP_STORY_LIMIT
) -> Dict:
    items = _fetch_top_items(sb, limit, source_ids)
    if not items:
        raise HTTPException(
            status_code=404,
            detail="No items found. Add sources and ingest content first.",
        )

    curated = [_ensure_story_format(dict(it)) for it in items]

    intro = "Here are the top stories and trends you should know today."
    trends = [it["title"] for it in curated[:3]]
    html_body, text_body = render_newsletter(intro, curated, trends)
    return {
        "items": curated,
        "html": html_body,
        "text": text_body,
        "intro": intro,
        "trends": trends,
    }


@router.post("/generate")
def generate_newsletter(
    source_ids: Optional[List[int]] = Body(default=None, embed=True)
):
    sb = get_client()
    logger.info("Generating newsletter (source_ids=%s)", source_ids)
    newsletter = _build_newsletter(sb, source_ids)
    return {
        "html": newsletter["html"],
        "text": newsletter["text"],
        "stories": [
            {"title": item["title"], "summary": item["summary"], "url": item["url"]}
            for item in newsletter["items"]
        ],
    }


@router.post("/pipeline")
def run_pipeline(payload: PipelineRequest):
    sb = get_client()
    steps = []
    current_stage = "source"
    selected_ids: Optional[Set[int]] = (
        set(payload.source_ids) if payload and payload.source_ids else None
    )

    logger.info(
        "Pipeline requested (source_url=%s, ingest_existing=%s, source_ids=%s)",
        payload.source_url,
        payload.ingest_existing,
        payload.source_ids,
    )

    try:
        # Optional: add a new source supplied by the user.
        if payload.source_url:
            existing = (
                sb.table("sources")
                .select("id")
                .eq("url", str(payload.source_url))
                .limit(1)
                .execute()
                .data
            )
            if not existing:
                insert_res = (
                    sb.table("sources")
                    .insert(
                        {
                            "name": payload.source_name or str(payload.source_url),
                            "url": str(payload.source_url),
                            "type": "rss",
                        }
                    )
                    .execute()
                )
                new_id = insert_res.data[0]["id"]
                if selected_ids is not None:
                    selected_ids.add(new_id)
                steps.append(
                    {
                        "stage": "source",
                        "status": "completed",
                        "action": "added",
                        "source_id": new_id,
                    }
                )
            else:
                if selected_ids is not None:
                    selected_ids.add(existing[0]["id"])
                steps.append(
                    {"stage": "source", "status": "completed", "action": "existing"}
                )
        else:
            steps.append({"stage": "source", "status": "skipped"})

        # Resolve which sources to use for the rest of the pipeline.
        source_query = sb.table("sources").select("id,url,name")
        if selected_ids:
            source_query = source_query.in_("id", list(selected_ids))
        source_records = source_query.execute().data or []
        if not source_records:
            steps.append(
                {
                    "stage": "source",
                    "status": "error",
                    "message": "No sources available. Select or add at least one.",
                }
            )
            return JSONResponse(
                status_code=400,
                content={
                    "error": "No sources selected. Add or select at least one source.",
                    "steps": steps,
                },
            )

        used_source_ids = [row["id"] for row in source_records]
        if selected_ids is None:
            selected_ids = set(used_source_ids)

        # Fetch data (ingest feeds)
        current_stage = "fetch"
        total_inserted = 0
        if payload.ingest_existing:
            for source in source_records:
                inserted, _ = ingest_feed(sb, source)
                total_inserted += inserted
            steps.append(
                {
                    "stage": "fetch",
                    "status": "completed",
                    "inserted": total_inserted,
                }
            )
        else:
            steps.append({"stage": "fetch", "status": "skipped"})

        # Curate & summarize top 10 stories
        current_stage = "curate"
        newsletter = _build_newsletter(sb, used_source_ids)
        steps.append(
            {
                "stage": "curate",
                "status": "completed",
                "stories": len(newsletter["items"]),
            }
        )
        steps.append({"stage": "summarize", "status": "completed"})
        steps.append(
            {
                "stage": "preview",
                "status": "completed" if newsletter["html"] else "pending",
            }
        )

        response = {
            "steps": steps,
            "html": newsletter["html"],
            "text": newsletter["text"],
            "stories": [
                {
                    "title": item["title"],
                    "summary": item["summary"],
                    "url": item["url"],
                }
                for item in newsletter["items"]
            ],
            "used_source_ids": used_source_ids,
        }
        logger.info("Pipeline completed successfully")
        return response
    except HTTPException as exc:
        logger.warning(
            "Pipeline aborted with HTTPException at stage %s: %s",
            current_stage,
            exc.detail,
        )
        steps.append(
            {"stage": current_stage, "status": "error", "message": exc.detail}
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail, "steps": steps},
        )
    except Exception as exc:
        logger.exception("Pipeline failed at stage %s: %s", current_stage, exc)
        steps.append(
            {"stage": current_stage, "status": "error", "message": str(exc)}
        )
        return JSONResponse(
            status_code=500,
            content={"error": "Pipeline failed.", "steps": steps},
        )


@router.post("/send")
def send_newsletter(payload: Optional[SendRequest] = Body(default=None)):
    sb = get_client()
    source_ids = payload.source_ids if payload else None
    html_override = payload.html if payload and payload.html else None
    text_override = payload.text if payload and payload.text else None

    logger.info(
        "Send requested (source_ids=%s, html_override=%s, text_override=%s, email=%s)",
        source_ids,
        bool(html_override),
        bool(text_override),
        payload.email_to if payload else None,
    )

    newsletter = None
    if html_override is None or text_override is None or source_ids:
        newsletter = _build_newsletter(sb, source_ids)

    if not newsletter and not html_override:
        raise HTTPException(
            status_code=400,
            detail="No newsletter content available. Run the pipeline first.",
        )

    if newsletter is None:
        newsletter = {"html": "", "text": ""}

    html_body = html_override or newsletter.get("html") or ""
    if not html_body.strip():
        raise HTTPException(
            status_code=400,
            detail="Newsletter HTML is empty. Provide edited content or rerun the pipeline.",
        )

    text_body = text_override or newsletter.get("text") or ""
    if not text_body.strip():
        text_body = strip_markup(html_body)

    subject = f"CreatorPulse Daily - {datetime.utcnow().date()}"
    email_to = payload.email_to if payload and payload.email_to else None
    logger.info(
        "Dispatching newsletter email with subject '%s' (recipient=%s)",
        subject,
        email_to or "default",
    )
    send_email(subject, html_body, text_body, recipient=email_to)

    try:
        sb.table("history").insert(
            {"run_date": datetime.utcnow().isoformat(), "status": "sent"}
        ).execute()
    except Exception:
        logger.warning("Failed to record send event in history table", exc_info=True)

    return {"status": "sent", "subject": subject}
