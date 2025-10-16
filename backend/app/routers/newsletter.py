from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.core.supabase_client import get_client
from app.core.llm_utils import summarize_article, render_newsletter
from app.core.emailer import send_email

router = APIRouter()

@router.post("/generate")
def generate_newsletter():
    sb = get_client()
    # Fetch latest 5 items
    items = sb.table("items").select("*").order("published", desc=True).limit(5).execute().data
    if not items:
        raise HTTPException(status_code=404, detail="No items found. Add sources and ingest content first.")
    # Summarize each
    for it in items:
        text = it.get("content") or it.get("summary") or it.get("title", "")
        it["summary"] = summarize_article(text)
    # Simple intro + trends
    intro = "Here are the most relevant stories and trends curated for you today."
    trends = [it["title"] for it in items[:3]]
    markdown = render_newsletter(intro, items, trends)
    return {"markdown": markdown}

@router.post("/send")
def send_newsletter():
    sb = get_client()
    # Reuse last generation if stored, else generate on the fly
    items = sb.table("items").select("*").order("published", desc=True).limit(5).execute().data
    if not items:
        raise HTTPException(status_code=404, detail="No items to send.")
    for it in items:
        text = it.get("content") or it.get("summary") or it.get("title", "")
        it["summary"] = summarize_article(text)
    intro = "Here are the most relevant stories and trends curated for you today."
    trends = [it["title"] for it in items[:3]]
    markdown = render_newsletter(intro, items, trends)
    subject = f"CreatorPulse Daily — {datetime.utcnow().date()}"
    send_email(subject, markdown)
    # Log history (best-effort)
    try:
        sb.table("history").insert({"run_date": datetime.utcnow().isoformat(), "status": "sent"}).execute()
    except Exception:
        pass
    return {"status": "sent"}
