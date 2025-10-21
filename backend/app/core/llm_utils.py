import os
from html import escape, unescape
from typing import Dict, Tuple
from dotenv import load_dotenv
import google.generativeai as genai
import openai
from app.core.content_utils import strip_markup

# Load .env values so keys resolve during module import.
load_dotenv()

# Configure Gemini (default)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Configure OpenAI (fallback)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY


def _sanitize_summary(value: str) -> str:
    text = strip_markup(value)
    # Normalize multiple spaces/new lines into single line with explicit breaks.
    normalized = " ".join(text.split())
    # Preserve deliberate sentence separators by reintroducing newline before the CTA.
    normalized = normalized.replace(" Why it matters:", "\nWhy it matters:")
    normalized = normalized.replace(" WHY IT MATTERS:", "\nWhy it matters:")
    return normalized.strip()


def summarize_article(text: str) -> str:
    cleaned_text = strip_markup(text)
    if not cleaned_text:
        cleaned_text = (text or "").strip()

    prompt = (
        "Summarize the following article in plain English using 2-3 sentences. "
        "End with a final sentence that starts with 'Why it matters:' explaining the impact. "
        "Do not include markup, HTML tags, or bullet lists; keep it concise prose.\n\n"
        f"{cleaned_text}"
    )
    # Try Gemini first
    try:
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY not set")
        model = genai.GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content(prompt)
        content = resp.text or ""
        if content.strip():
            return _sanitize_summary(content)
        # Fall through to OpenAI if empty
    except Exception:
        pass

    # Fallback: OpenAI
    try:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY not set")
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.3,
        )
        return _sanitize_summary(resp.choices[0].message["content"])
    except Exception:
        # Last resort: truncate input
        return (cleaned_text or "")[:500]


def normalize_summary(value: str) -> str:
    return _sanitize_summary(value)


def summary_is_informative(value: str) -> bool:
    text = strip_markup(value or "")
    if not text:
        return False
    words = text.split()
    if len(words) < 10:
        return False
    if "why it matters" not in text.lower():
        return False
    placeholders = {"comments", "comment", "read more", "n/a", "na"}
    if text.strip().lower() in placeholders:
        return False
    return True


def fallback_summary(title: str) -> str:
    headline = (title or "This story").strip()
    return (
        f"{headline} is developing; for full context, explore the linked source. "
        "Why it matters: Staying close to the original report keeps you ahead of new updates."
    )


def _parse_headline_summary(raw: str, fallback_title: str) -> Dict[str, str]:
    headline = fallback_title.strip() or "Untitled"
    summary_chunks = []
    for line in raw.splitlines():
        parsed = line.strip()
        lower = parsed.lower()
        if lower.startswith("headline:"):
            headline_candidate = parsed.split(":", 1)[1].strip()
            if headline_candidate:
                headline = headline_candidate
        elif lower.startswith("summary:"):
            summary_candidate = parsed.split(":", 1)[1].strip()
            if summary_candidate:
                summary_chunks.append(summary_candidate)
        elif parsed:
            summary_chunks.append(parsed)

    summary_text = " ".join(summary_chunks) if summary_chunks else raw
    summary = _sanitize_summary(summary_text)
    return {"headline": headline, "summary": summary}


def summarize_story(text: str, fallback_title: str) -> Dict[str, str]:
    cleaned_text = strip_markup(text)
    if not cleaned_text:
        cleaned_text = (text or fallback_title or "").strip()

    prompt = (
        "You are a newsletter editor. Produce a concise, informative brief.\n"
        "Respond with exactly two lines:\n"
        "Headline: <A sharp news-style headline in Title Case, max 12 words>\n"
        "Summary: <Two sentences of plain text ending with 'Why it matters:' insight>\n"
        "Do not include HTML, bullets, or any additional commentary.\n\n"
        f"{cleaned_text}"
    )

    try:
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY not set")
        model = genai.GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content(prompt)
        content = (resp.text or "").strip()
        if content:
            return _parse_headline_summary(content, fallback_title)
    except Exception:
        pass

    try:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY not set")
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=260,
            temperature=0.3,
        )
        content = resp.choices[0].message["content"].strip()
        if content:
            return _parse_headline_summary(content, fallback_title)
    except Exception:
        pass

    return {
        "headline": fallback_title.strip() or "Untitled",
        "summary": normalize_summary(cleaned_text[:500]),
    }


def render_newsletter(intro: str, items: list, trends: list) -> Tuple[str, str]:
    intro_text = (intro or "").strip()
    intro_html = escape(intro_text).replace("\n", "<br>")

    text_lines = ["CreatorPulse Daily", ""]
    if intro_text:
        text_lines.append(intro_text)
        text_lines.append("")

    item_blocks = []
    total_items = len(items)
    if total_items:
        text_lines.append("Top Stories")
        text_lines.append("")

    for idx, it in enumerate(items, start=1):
        raw_title = it.get("title", f"Story {idx}") or f"Story {idx}"
        title = unescape(raw_title)
        url = it.get("url", "")
        summary_raw = (it.get("summary", "") or "").strip()
        summary = unescape(summary_raw)

        text_lines.append(f"{idx}. {title}")
        if url:
            text_lines.append(url)
        if summary:
            text_lines.append(summary)
        text_lines.append("")

        title_html = escape(title)
        summary_html = escape(summary).replace("\n", "<br>")
        summary_section = ""
        if summary_html:
            summary_section = (
                f'<p style="margin:0 0 12px;font-size:15px;line-height:1.6;color:#1f2933;">'
                f"{summary_html}"
                "</p>"
            )

        border_style = "border-bottom:1px solid #e5e7eb;" if idx != total_items else ""
        link_html = ""
        if url:
            safe_url = escape(url, quote=True)
            link_html = (
                f'<a href="{safe_url}" '
                'style="color:#2563eb;text-decoration:none;font-weight:500;">'
                "Read the full story -></a>"
            )

        item_blocks.append(
            (
                f'<div style="margin-bottom:24px;padding-bottom:24px;{border_style}">'
                f'<div style="font-size:12px;color:#9ca3af;text-transform:uppercase;letter-spacing:0.08em;">'
                f"Story {idx}"
                "</div>"
                f'<h3 style="margin:8px 0 12px;font-size:18px;color:#111827;">{title_html}</h3>'
                f"{summary_section}"
                f"{link_html}"
                "</div>"
            )
        )

    if not item_blocks:
        item_blocks.append(
            (
                '<p style="margin:0;font-size:15px;line-height:1.6;color:#4b5563;">'
                "No new stories were available at this time."
                "</p>"
            )
        )

    trends_section = ""
    if trends:
        text_lines.append("Trends to Watch")
        for raw_t in trends:
            if not raw_t:
                continue
            clean_t = unescape(raw_t)
            text_lines.append(f"- {clean_t}")
        text_lines.append("")
        trend_items = "".join(
            f'<li style="margin-bottom:8px;">{escape(unescape(t))}</li>'
            for t in trends
            if t
        )
        trends_section = (
            '<div style="margin-top:24px;">'
            '<h2 style="margin:0 0 12px;font-size:17px;color:#111827;">Trends to Watch</h2>'
            '<ul style="margin:0;padding-left:20px;color:#374151;font-size:15px;line-height:1.6;">'
            f"{trend_items}"
            "</ul>"
            "</div>"
        )

    text_body = "\n".join(line for line in text_lines if line is not None).strip()
    items_html = "".join(item_blocks)
    html_body = (
        '<div style="background-color:#f5f7fb;padding:24px 0;">'
        '<table role="presentation" cellpadding="0" cellspacing="0" width="100%" '
        "style=\"max-width:640px;margin:0 auto;background-color:#ffffff;border-radius:12px;overflow:hidden;"
        "font-family:'Segoe UI',Arial,sans-serif;color:#1f2933;\">"
        "<tr>"
        '<td style="background-color:#111827;padding:28px 32px;">'
        '<h1 style="margin:0;font-size:24px;color:#ffffff;">CreatorPulse Daily</h1>'
        f'<p style="margin:12px 0 0;font-size:15px;line-height:1.6;color:#f3f4f6;">{intro_html}</p>'
        "</td>"
        "</tr>"
        "<tr>"
        '<td style="padding:32px;">'
        '<h2 style="margin:0 0 16px;font-size:18px;color:#111827;">Top Stories</h2>'
        f"{items_html}"
        f"{trends_section}"
        "</td>"
        "</tr>"
        "<tr>"
        '<td style="background-color:#f3f4f6;padding:16px 32px;font-size:12px;color:#6b7280;text-align:center;">'
        "You are receiving this update because you follow CreatorPulse."
        "</td>"
        "</tr>"
        "</table>"
        "</div>"
    )

    return html_body, text_body
