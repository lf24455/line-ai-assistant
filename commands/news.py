from __future__ import annotations

from services.news import get_market_news


def format_news_message() -> str:
    items = get_market_news(limit=5)
    lines = ["📰 市場新聞", "━━━━━━━━━━━━━━", ""]
    for index, item in enumerate(items, start=1):
        source = item.get("source") or "新聞來源"
        published = item.get("published_at") or ""
        meta = "｜".join(part for part in (source, published) if part)
        lines.append(f"{index}. {item.get('title', '無標題')}")
        if meta:
            lines.append(f"   {meta}")
        lines.append("")
    lines.append("新聞標題由公開 RSS 彙整，內容請以原始媒體為準。")
    return "\n".join(lines).strip()
