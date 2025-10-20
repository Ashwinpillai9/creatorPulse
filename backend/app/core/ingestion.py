from __future__ import annotations

from datetime import datetime
import time
from typing import Dict, Iterable, Tuple

import feedparser

from app.core.content_utils import fetch_article_text, strip_markup
from app.core.llm_utils import summarize_story, normalize_summary


def _existing_urls(sb, source_id: int) -> set[str]:
    try:
        existing = (
            sb.table("items")
            .select("url")
            .eq("source_id", source_id)
            .execute()
            .data
        )
        return {row["url"] for row in existing if row.get("url")}
    except Exception:
        return set()


def ingest_feed(sb, source: Dict) -> Tuple[int, Iterable[Dict]]:
    """
    Pulls entries from the RSS feed, fetches article bodies, generates
    news-style headlines + summaries, and upserts items into Supabase.
    Returns a tuple of (inserted_count, processed_items).
    """
    source_id = source["id"]
    feed_url = source["url"]
    existing_urls = _existing_urls(sb, source_id)

    feed = feedparser.parse(feed_url)
    if feed.bozo:
        print(
            f"Warning: Ill-formed feed at {feed_url}. "
            f"Reason: {feed.bozo_exception}"
        )

    items_to_insert = []
    processed_items = []
    for entry in feed.entries:
        link = entry.get("link", "")
        if not link or link in existing_urls:
            continue

        # Convert published time to ISO 8601 format with timezone awareness
        published_time = datetime.now().isoformat()
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published_time = datetime.fromtimestamp(
                time.mktime(entry.published_parsed)
            ).isoformat()

        raw_content = entry.get("content", [{}])[0].get("value", "") if entry.get("content") else ""
        raw_summary = entry.get("summary", "")
        article_text = fetch_article_text(link)
        if not article_text:
            article_text = strip_markup(raw_content) or strip_markup(raw_summary)

        summary_source = (
            article_text
            or strip_markup(raw_summary)
            or entry.get("title", "")
        )

        story = summarize_story(summary_source, entry.get("title", "Untitled"))
        if not story["summary"]:
            story["summary"] = normalize_summary(summary_source)

        item = {
            "source_id": source_id,
            "title": story["headline"],
            "url": link,
            "content": article_text,
            "summary": story["summary"],
            "published": published_time,
        }
        items_to_insert.append(item)
        processed_items.append(item)

    if not items_to_insert:
        return 0, processed_items

    res = sb.table("items").upsert(items_to_insert, on_conflict="url").execute()
    inserted_count = len(res.data) if getattr(res, "data", None) else len(items_to_insert)
    return inserted_count, processed_items
