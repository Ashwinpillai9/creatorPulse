from fastapi import APIRouter, HTTPException
from app.core.supabase_client import get_client
from app.core.schemas import SourceIn
from app.core.ingestion import ingest_feed

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
    source_res = (
        sb.table("sources")
        .select("id,url,name")
        .eq("url", url)
        .limit(1)
        .execute()
        .data
    )
    if not source_res:
        raise HTTPException(status_code=404, detail="Source URL not found.")
    source = source_res[0]

    inserted_count, processed_items = ingest_feed(sb, source)

    if not inserted_count:
        return {
            "status": "success",
            "inserted": 0,
            "message": "No new items found in feed.",
        }

    return {
        "status": "success",
        "inserted": inserted_count,
        "processed": len(processed_items),
    }
