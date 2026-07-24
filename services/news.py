from __future__ import annotations

import html
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from datetime import datetime
from email.utils import parsedate_to_datetime
from threading import Lock
from typing import Any
from urllib.parse import quote_plus

import requests

from config import NEWS_HEADERS, NEWS_QUERY

NEWS_CACHE_TTL_SECONDS = 300
NEWS_STALE_CACHE_SECONDS = 1800
NEWS_LIMIT = 6

_cache: tuple[float, list[dict[str, Any]]] | None = None
_cache_lock = Lock()


@dataclass
class NewsItem:
    title: str
    source: str
    published_at: str
    link: str


def _cache_get(max_age: int) -> list[dict[str, Any]] | None:
    with _cache_lock:
        item = _cache
    if not item:
        return None
    saved_at, value = item
    if time.time() - saved_at > max_age:
        return None
    return [dict(entry) for entry in value]


def _cache_set(value: list[dict[str, Any]]) -> None:
    global _cache
    with _cache_lock:
        _cache = (time.time(), [dict(entry) for entry in value])


def _clean_title(raw_title: str) -> tuple[str, str]:
    text = html.unescape(raw_title or "").strip()
    if " - " in text:
        title, source = text.rsplit(" - ", 1)
        return title.strip(), source.strip()
    return text, "Google News"


def _format_published(raw_date: str) -> str:
    if not raw_date:
        return ""
    try:
        parsed = parsedate_to_datetime(raw_date)
        return parsed.astimezone().strftime("%m/%d %H:%M")
    except (TypeError, ValueError, OverflowError):
        return raw_date[:16]


def _rss_url() -> str:
    query = quote_plus(NEWS_QUERY)
    return (
        "https://news.google.com/rss/search"
        f"?q={query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    )


def _fetch_news() -> list[dict[str, Any]]:
    response = requests.get(_rss_url(), headers=NEWS_HEADERS, timeout=12)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    output: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in root.findall("./channel/item"):
        title, source = _clean_title(item.findtext("title", default=""))
        if not title or title in seen:
            continue
        seen.add(title)
        news = NewsItem(
            title=title,
            source=source,
            published_at=_format_published(item.findtext("pubDate", default="")),
            link=(item.findtext("link", default="") or "").strip(),
        )
        output.append(asdict(news))
        if len(output) >= NEWS_LIMIT:
            break

    if not output:
        raise ValueError("新聞來源沒有回傳內容")
    return output


def get_market_news(limit: int = 3, force_refresh: bool = False) -> list[dict[str, Any]]:
    limit = max(1, min(limit, NEWS_LIMIT))
    if not force_refresh:
        cached = _cache_get(NEWS_CACHE_TTL_SECONDS)
        if cached:
            return cached[:limit]

    try:
        items = _fetch_news()
        _cache_set(items)
        return items[:limit]
    except Exception:
        stale = _cache_get(NEWS_STALE_CACHE_SECONDS)
        if stale:
            return stale[:limit]
        raise
