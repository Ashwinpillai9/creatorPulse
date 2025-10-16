from fastapi import APIRouter
from app.core.supabase_client import get_client
from app.core.schemas import FeedbackIn

router = APIRouter()

@router.post("")
def submit_feedback(fb: FeedbackIn):
    sb = get_client()
    res = sb.table("feedback").insert({
        "item_id": fb.item_id,
        "thumbs": fb.thumbs,
        "diff": fb.diff_json or {}
    }).execute()
    return res.data
