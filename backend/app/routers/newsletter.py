from datetime import datetime
from fastapi import APIRouter, HTTPException

from app.core.emailer import send_email
from app.core.llm_utils import render_newsletter, summarize_article
from app.core.supabase_client import get_client

router = APIRouter()


@router.post("/generate")
def generate_newsletter():
    sb = get_client()
    items = (
        sb.table("items")
        .select("*")
        .order("published", desc=True)
        .limit(5)
        .execute()
        .data
    )
    if not items:
        raise HTTPException(
            status_code=404,
            detail="No items found. Add sources and ingest content first.",
        )

    for it in items:
        text = it.get("content") or it.get("summary") or it.get("title", "")
        it["summary"] = summarize_article(text)

    intro = "Here are the most relevant stories and trends curated for you today."
    trends = [it["title"] for it in items[:3]]
    html_body, text_body = render_newsletter(intro, items, trends)
    return {"html": html_body, "text": text_body}


@router.post("/send")
def send_newsletter():
    sb = get_client()
    items = (
        sb.table("items")
        .select("*")
        .order("published", desc=True)
        .limit(5)
        .execute()
        .data
    )
    if not items:
        raise HTTPException(status_code=404, detail="No items to send.")

    for it in items:
        text = it.get("content") or it.get("summary") or it.get("title", "")
        it["summary"] = summarize_article(text)

    intro = "Here are the most relevant stories and trends curated for you today."
    trends = [it["title"] for it in items[:3]]
    html_body, text_body = render_newsletter(intro, items, trends)
    subject = f"CreatorPulse Daily - {datetime.utcnow().date()}"
    send_email(subject, html_body, text_body)

    try:
        sb.table("history").insert(
            {"run_date": datetime.utcnow().isoformat(), "status": "sent"}
        ).execute()
    except Exception:
        pass

    return {"status": "sent", "subject": subject}
