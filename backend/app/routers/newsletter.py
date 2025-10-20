from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, HTTPException

from app.core.emailer import send_email
from app.core.ingestion import ingest_feed
from app.core.llm_utils import (
    normalize_summary,
    render_newsletter,
    summarize_story,
)
from app.core.schemas import PipelineRequest
from app.core.supabase_client import get_client

router = APIRouter()

TOP_STORY_LIMIT = 10


def _fetch_top_items(sb, limit: int = TOP_STORY_LIMIT) -> List[Dict]:
    res = (
        sb.table("items")
        .select("*")
        .order("published", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


def _ensure_story_format(item: Dict) -> Dict:
    fallback_title = item.get("title") or "Untitled"
    summary = item.get("summary") or ""

    if summary and "why it matters" in summary.lower():
        item["summary"] = normalize_summary(summary)
        item["title"] = fallback_title
        return item

    article_text = item.get("content") or summary or fallback_title
    story = summarize_story(article_text, fallback_title)
    item["title"] = story["headline"]
    item["summary"] = story["summary"]
    return item


def _build_newsletter(sb) -> Dict:
    items = _fetch_top_items(sb, TOP_STORY_LIMIT)
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
def generate_newsletter():
    sb = get_client()
    newsletter = _build_newsletter(sb)
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
            sb.table("sources").insert(
                {
                    "name": payload.source_name or str(payload.source_url),
                    "url": str(payload.source_url),
                    "type": "rss",
                }
            ).execute()
            steps.append({"stage": "source", "status": "added"})
        else:
            steps.append({"stage": "source", "status": "existing"})
    else:
        steps.append({"stage": "source", "status": "skipped"})

    # Fetch data (ingest feeds)
    total_inserted = 0
    if payload.ingest_existing:
        sources = sb.table("sources").select("id,url,name").execute().data or []
        for source in sources:
            inserted, _ = ingest_feed(sb, source)
            total_inserted += inserted
        steps.append({"stage": "fetch", "status": "completed", "inserted": total_inserted})
    else:
        steps.append({"stage": "fetch", "status": "skipped"})

    # Curate & summarize top 10 stories
    newsletter = _build_newsletter(sb)
    steps.append({"stage": "curate", "status": "completed", "stories": len(newsletter["items"])})
    steps.append({"stage": "summarize", "status": "completed"})

    return {
        "steps": steps,
        "html": newsletter["html"],
        "text": newsletter["text"],
        "stories": [
            {"title": item["title"], "summary": item["summary"], "url": item["url"]}
            for item in newsletter["items"]
        ],
    }


@router.post("/send")
def send_newsletter():
    sb = get_client()
    newsletter = _build_newsletter(sb)
    subject = f"CreatorPulse Daily - {datetime.utcnow().date()}"
    send_email(subject, newsletter["html"], newsletter["text"])

    try:
        sb.table("history").insert(
            {"run_date": datetime.utcnow().isoformat(), "status": "sent"}
        ).execute()
    except Exception:
        pass

    return {"status": "sent", "subject": subject}
