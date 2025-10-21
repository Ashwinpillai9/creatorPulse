from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Dict, Iterable, Tuple

import feedparser

from app.core.content_utils import fetch_article_text, strip_markup
from app.core.llm_utils import (
    fallback_summary,
    normalize_summary,
    summarize_story,
    summary_is_informative,
)

logger = logging.getLogger(__name__)


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    # Remove NULL bytes or other control chars that Supabase/Postgres rejects.
    return value.replace("\x00", "")


def _existing_urls(sb, source_id: int) -> set[str]:
    try:
        existing = (
            sb.table("items")
            .select("url")
            .eq("source_id", source_id)
            .execute()
            .data
        )
        urls = {row["url"] for row in existing if row.get("url")}
        logger.debug("Found %d existing URLs for source %s", len(urls), source_id)
        return urls
    except Exception:
        logger.exception("Failed to fetch existing URLs for source %s", source_id)
        return set()


def ingest_feed(sb, source: Dict) -> Tuple[int, Iterable[Dict]]:
    """
    Pulls entries from the RSS feed, fetches article bodies, generates
    news-style headlines + summaries, and upserts items into Supabase.
    Returns a tuple of (inserted_count, processed_items).
    """
    source_id = source["id"]
    feed_url = source["url"]
    logger.info("Starting ingestion for source %s (%s)", source_id, feed_url)

    existing_urls = _existing_urls(sb, source_id)

    feed = feedparser.parse(feed_url)
    if feed.bozo:
        logger.warning(
            "Feed parser reported a problem for %s - %s",
            feed_url,
            getattr(feed, "bozo_exception", "unknown error"),
        )

    items_to_insert = []
    processed_items = []
    for entry in feed.entries:
        link = entry.get("link", "")
        if not link:
            logger.debug("Skipping entry with no link from %s", feed_url)
            continue
        if link in existing_urls:
            logger.debug("Skipping already ingested link %s", link)
            continue

        published_time = datetime.now().isoformat()
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published_time = datetime.fromtimestamp(
                time.mktime(entry.published_parsed)
            ).isoformat()

        raw_content = (
            entry.get("content", [{}])[0].get("value", "")
            if entry.get("content")
            else ""
        )
        raw_summary = entry.get("summary", "")

        article_text = fetch_article_text(link)
        if not article_text:
            article_text = strip_markup(raw_content) or strip_markup(raw_summary)

        summary_source = (
            article_text or strip_markup(raw_summary) or entry.get("title", "")
        )

        title = entry.get("title", "Untitled")
        story = summarize_story(summary_source, title)

        if not summary_is_informative(story["summary"]):
            alternate_source = " ".join(
                filter(
                    None,
                    [
                        title,
                        strip_markup(raw_summary),
                        strip_markup(raw_content),
                        article_text,
                    ],
                )
            )
            if alternate_source.strip():
                alt_story = summarize_story(alternate_source, title)
                if summary_is_informative(alt_story["summary"]):
                    story = alt_story

        if not summary_is_informative(story["summary"]):
            logger.debug(
                "Using fallback summary for link %s (title: %s)", link, story["headline"]
            )
            story["summary"] = fallback_summary(story["headline"])

        story["summary"] = normalize_summary(_clean_text(story["summary"]) or "")

        item = {
            "source_id": source_id,
            "title": _clean_text(story["headline"]),
            "url": link,
            "content": _clean_text(article_text),
            "summary": _clean_text(story["summary"]),
            "published": published_time,
        }
        items_to_insert.append(item)
        processed_items.append(item)

    if not items_to_insert:
        logger.info("No new items found for source %s", source_id)
        return 0, processed_items

    res = sb.table("items").upsert(items_to_insert, on_conflict="url").execute()
    inserted_count = (
        len(res.data) if getattr(res, "data", None) else len(items_to_insert)
    )
    logger.info(
        "Ingestion completed for source %s - %d new item(s)",
        source_id,
        inserted_count,
    )
    return inserted_count, processed_items
