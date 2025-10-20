from pydantic import BaseModel, HttpUrl
from typing import Optional, List

class SourceIn(BaseModel):
    name: str
    url: HttpUrl
    type: str  # "rss" | "youtube" | "alert"

class Source(SourceIn):
    id: int

class FeedbackIn(BaseModel):
    item_id: int
    thumbs: str  # "up" | "down"
    diff_json: Optional[dict] = None

class NewsletterDraft(BaseModel):
    markdown: str


class PipelineRequest(BaseModel):
    source_name: Optional[str] = None
    source_url: Optional[HttpUrl] = None
    ingest_existing: bool = True
