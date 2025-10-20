import requests
from bs4 import BeautifulSoup
from html import unescape
from typing import Optional

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)


def strip_markup(value: Optional[str]) -> str:
    if not value:
        return ""
    soup = BeautifulSoup(value, "html.parser")
    for tag in soup(
        [
            "script",
            "style",
            "noscript",
            "svg",
            "path",
            "picture",
            "source",
            "iframe",
            "form",
        ]
    ):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return unescape(" ".join(text.split()))


def _extract_main_content(soup: BeautifulSoup) -> str:
    for selector in ["article", "main"]:
        node = soup.find(selector)
        if node:
            return node.get_text(separator=" ", strip=True)
    if soup.body:
        return soup.body.get_text(separator=" ", strip=True)
    return soup.get_text(separator=" ", strip=True)


def fetch_article_text(url: str, timeout: int = 10) -> str:
    if not url:
        return ""
    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
    except Exception:
        return ""

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(
        [
            "script",
            "style",
            "noscript",
            "svg",
            "path",
            "picture",
            "source",
            "iframe",
            "form",
            "header",
            "footer",
            "aside",
            "figure",
        ]
    ):
        tag.decompose()

    extracted = _extract_main_content(soup)
    return unescape(" ".join(extracted.split()))
