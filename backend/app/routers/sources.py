from fastapi import APIRouter, HTTPException
from app.core.supabase_client import get_client
from app.core.schemas import SourceIn
import feedparser
from datetime import datetime
import time

router = APIRouter()

@router.get("")
def list_sources():
    sb = get_client()
    res = sb.table("sources").select("*").execute()
    return res.data

@router.post("")
def add_source(src: SourceIn):
    sb = get_client()
    # Basic uniqueness by URL
    existing = sb.table("sources").select("id").eq("url", str(src.url)).execute().data
    if existing:
        raise HTTPException(status_code=409, detail="Source already exists")
    res = sb.table("sources").insert({"name": src.name, "url": str(src.url), "type": src.type}).execute()
    return res.data

@router.delete("")
def delete_source(url: str):
    sb = get_client()
    res = sb.table("sources").delete().eq("url", url).execute()
    return {"deleted": res.count if hasattr(res, "count") else True}

@router.post("/ingest")
def ingest_source(url: str):
    sb = get_client()
    # 1. Get source_id from URL
    source_res = sb.table("sources").select("id").eq("url", url).limit(1).execute().data
    if not source_res:
        raise HTTPException(status_code=404, detail="Source URL not found.")
    source_id = source_res[0]['id']

    # 2. Fetch and parse feed
    feed = feedparser.parse(url)
    if feed.bozo:
        print(f"Warning: Ill-formed feed at {url}. Reason: {feed.bozo_exception}")

    # 3. Prepare items for insertion
    items_to_insert = []
    for entry in feed.entries:
        # Convert published time to ISO 8601 format with timezone
        published_time = datetime.now().isoformat()
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed)).isoformat()

        item = {
            "source_id": source_id,
            "title": entry.get("title", "No Title"),
            "url": entry.get("link", ""),
            "content": entry.get("content", [{}])[0].get("value", ""),
            "summary": entry.get("summary", ""),
            "published": published_time,
        }
        # Skip items without a URL, as it's our unique key
        if item["url"]:
            items_to_insert.append(item)

    if not items_to_insert:
        return {"status": "success", "inserted": 0, "message": "No new items found in feed."}

    # 4. Upsert items into DB, ignoring duplicates based on URL
    res = sb.table("items").upsert(items_to_insert, on_conflict="url").execute()

    return {"status": "success", "inserted": len(res.data)}
