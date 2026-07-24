from __future__ import annotations

import time
from threading import Lock
from typing import Any

from config import OPENAI_API_KEY, OPENAI_MODEL

AI_CACHE_TTL_SECONDS = 300
_cache: dict[str, tuple[float, str]] = {}
_cache_lock = Lock()


def _cache_get(key: str) -> str | None:
    with _cache_lock:
        item = _cache.get(key)
    if not item:
        return None
    saved_at, value = item
    if time.time() - saved_at > AI_CACHE_TTL_SECONDS:
        return None
    return value


def _cache_set(key: str, value: str) -> None:
    with _cache_lock:
        _cache[key] = (time.time(), value)


def _market_line(item: dict[str, Any]) -> str:
    name = item.get("name", "行情")
    if item.get("error"):
        return f"{name}: 無資料"
    price = item.get("price")
    change = item.get("change")
    percent = item.get("changePercent")
    return f"{name}: {price}, 漲跌 {change}, 漲跌幅 {percent}%"


def _fallback_analysis(quotes: dict[str, dict[str, Any]]) -> str:
    valid = [item for item in quotes.values() if not item.get("error")]
    if not valid:
        return "目前行情資料不足，請稍後再試。"

    positives = sum(1 for item in valid if float(item.get("changePercent") or 0) > 0)
    negatives = sum(1 for item in valid if float(item.get("changePercent") or 0) < 0)
    if positives > negatives:
        tone = "整體盤勢偏多"
    elif negatives > positives:
        tone = "整體盤勢偏弱"
    else:
        tone = "市場多空分歧"

    sox = quotes.get("sox", {})
    nasdaq = quotes.get("nasdaq", {})
    tw = quotes.get("taiex", {})
    focus: list[str] = []
    if not sox.get("error"):
        focus.append(f"費半 {float(sox.get('changePercent') or 0):+.2f}%")
    if not nasdaq.get("error"):
        focus.append(f"NASDAQ {float(nasdaq.get('changePercent') or 0):+.2f}%")
    if not tw.get("error"):
        focus.append(f"加權 {float(tw.get('changePercent') or 0):+.2f}%")

    suffix = "、".join(focus[:3])
    if suffix:
        return f"{tone}；{suffix}。留意短線波動與重要消息，不宜只憑單一指標追價。"
    return f"{tone}。留意短線波動與重要消息，不宜只憑單一指標追價。"


def analyze_market(
    quotes: dict[str, dict[str, Any]],
    news: list[dict[str, Any]],
    force_refresh: bool = False,
) -> str:
    fallback = _fallback_analysis(quotes)
    if not OPENAI_API_KEY:
        return fallback

    market_text = "\n".join(_market_line(item) for item in quotes.values())
    news_text = "\n".join(
        f"- {item.get('title', '')}（{item.get('source', '')}）" for item in news
    )
    cache_key = market_text + "\n" + news_text
    if not force_refresh:
        cached = _cache_get(cache_key)
        if cached:
            return cached

    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY, timeout=18.0, max_retries=1)
        response = client.responses.create(
            model=OPENAI_MODEL,
            instructions=(
                "你是台灣投資人的市場助理。請根據提供的行情與新聞，"
                "用繁體中文寫 2 到 3 句、最多 120 字的客觀市場摘要。"
                "指出盤勢偏多、偏空或震盪，以及最重要的觀察點。"
                "不要預測必漲必跌，不要給出買賣指令，結尾不需加免責聲明。"
            ),
            input=f"行情：\n{market_text}\n\n新聞：\n{news_text}",
            max_output_tokens=180,
        )
        result = (response.output_text or "").strip()
        if not result:
            return fallback
        _cache_set(cache_key, result)
        return result
    except Exception as error:
        print("OpenAI analysis error:", repr(error))
        return fallback
