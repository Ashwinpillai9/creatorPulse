import os
from dotenv import load_dotenv
import google.generativeai as genai
import openai

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

def summarize_article(text: str) -> str:
    prompt = (
        "Summarize the following in 2-3 crisp sentences. "
        "End with a 'Why it matters' line. Keep it factual, neutral, and scannable.\n\n"
        f"{text}"
    )
    # Try Gemini first
    try:
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY not set")
        model = genai.GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content(prompt)
        content = resp.text or ""
        if content.strip():
            return content.strip()
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
        return resp.choices[0].message["content"].strip()
    except Exception as e:
        # Last resort: truncate input
        return (text or "")[:500]

def render_newsletter(intro: str, items: list, trends: list) -> str:
    lines = []
    lines.append("# 📰 CreatorPulse Daily\n")
    lines.append(intro.strip() + "\n")
    lines.append("## Top 5\n")
    for idx, it in enumerate(items, start=1):
        title = it.get("title", f"Item {idx}")
        url = it.get("url", "")
        summary = it.get("summary", "")
        lines.append(f"**{idx}. {title}**")
        if url:
            lines.append(f"{url}")
        lines.append(summary + "\n")
    if trends:
        lines.append("## Trends to Watch\n")
        for t in trends:
            lines.append(f"- {t}")
    return "\n".join(lines)
