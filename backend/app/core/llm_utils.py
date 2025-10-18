import os
from html import escape, unescape
from typing import Tuple
from dotenv import load_dotenv
import google.generativeai as genai
import openai
from bs4 import BeautifulSoup

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


def _strip_markup(value: str) -> str:
    if not value:
        return ""
    # BeautifulSoup gracefully handles HTML, XML, and plain text inputs.
    soup = BeautifulSoup(value, "html.parser")
    # Remove scripts/styles that can add noise.
    for tag in soup(["script", "style"]):
        tag.decompose()
    cleaned = soup.get_text(separator=" ", strip=True)
    return unescape(cleaned)


def _sanitize_summary(value: str) -> str:
    text = _strip_markup(value)
    # Normalize multiple spaces/new lines into single line with explicit breaks.
    normalized = " ".join(text.split())
    # Preserve deliberate sentence separators by reintroducing newline before the CTA.
    normalized = normalized.replace(" Why it matters:", "\nWhy it matters:")
    normalized = normalized.replace(" WHY IT MATTERS:", "\nWhy it matters:")
    return normalized.strip()


def summarize_article(text: str) -> str:
    cleaned_text = _strip_markup(text)
    if not cleaned_text:
        cleaned_text = (text or "").strip()

    prompt = (
        "Summarize the following article in plain English using 2-3 sentences. "
        "End with a final sentence that starts with 'Why it matters:' explaining the impact. "
        "Do not include markup, HTML tags, or bullet lists—just concise prose.\n\n"
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
