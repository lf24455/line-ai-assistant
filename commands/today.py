from __future__ import annotations

from typing import Any

from services.ai import analyze_market
from services.global_market import get_quotes
from services.news import get_market_news


def _price(value: Any) -> str:
    try:
        number = float(value)
    except (ValueError, TypeError):
        return "無資料"
    decimals = 4 if abs(number) < 100 else 2
    return f"{number:,.{decimals}f}".rstrip("0").rstrip(".")


def _compact_line(data: dict[str, Any]) -> str:
    name = data.get("name", "行情")
    if data.get("error"):
        return f"{name}：暫無資料"
    change = float(data.get("change") or 0)
    percent = float(data.get("changePercent") or 0)
    icon = "▲" if change > 0 else "▼" if change < 0 else "－"
    return f"{name}：{_price(data.get('price'))} {icon}{abs(percent):.2f}%"


def _news_lines(items: list[dict[str, Any]]) -> str:
    if not items:
        return "暫時無法取得新聞"
    return "\n".join(
        f"{index}. {item.get('title', '無標題')}"
        for index, item in enumerate(items, start=1)
    )


def format_today_message() -> str:
    quotes = get_quotes(
        ["taiex", "tsmc", "0050", "dow", "nasdaq", "sox", "usd_twd"],
        include_taifex=True,
    )

    try:
        news = get_market_news(limit=3)
    except Exception as error:
        print("News error:", repr(error))
        news = []

    analysis = analyze_market(quotes, news)
    stale = any(item.get("cache") == "stale" for item in quotes.values())

    message = (
        "📅 今日市場懶人包\n"
        "━━━━━━━━━━━━━━\n\n"
        "🇹🇼 台灣\n"
        f"{_compact_line(quotes['taifex'])}\n"
        f"{_compact_line(quotes['taiex'])}\n"
        f"{_compact_line(quotes['tsmc'])}\n"
        f"{_compact_line(quotes['0050'])}\n\n"
        "🇺🇸 美國\n"
        f"{_compact_line(quotes['dow'])}\n"
        f"{_compact_line(quotes['nasdaq'])}\n"
        f"{_compact_line(quotes['sox'])}\n\n"
        "💵 匯率\n"
        f"{_compact_line(quotes['usd_twd'])}\n\n"
        "📰 今日三大新聞\n"
        f"{_news_lines(news)}\n\n"
        "🤖 AI 市場重點\n"
        f"{analysis}\n\n"
        "⚠️ 免費行情可能延遲，內容僅供資訊整理，不構成投資建議。"
    )
    if stale:
        message += "\n部分行情使用最近一次成功快取。"
    return message
