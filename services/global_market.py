from __future__ import annotations

import time
from datetime import datetime
from threading import Lock
from typing import Any
from urllib.parse import quote

import requests

from config import YAHOO_HEADERS
from services.numbers import parse_number
from services.market import get_market_data

CACHE_TTL_SECONDS = 15
STALE_CACHE_SECONDS = 600

SYMBOLS: dict[str, dict[str, str]] = {
    "taiex": {"symbol": "^TWII", "name": "加權指數"},
    "tsmc": {"symbol": "2330.TW", "name": "台積電"},
    "0050": {"symbol": "0050.TW", "name": "0050 元大台灣50"},
    "0056": {"symbol": "0056.TW", "name": "0056 元大高股息"},
    "00919": {"symbol": "00919.TW", "name": "00919 群益台灣精選高息"},
    "00940": {"symbol": "00940.TW", "name": "00940 元大台灣價值高息"},
    "dow": {"symbol": "^DJI", "name": "道瓊"},
    "sp500": {"symbol": "^GSPC", "name": "S&P 500"},
    "nasdaq": {"symbol": "^IXIC", "name": "NASDAQ"},
    "sox": {"symbol": "^SOX", "name": "費半"},
    "tsm_adr": {"symbol": "TSM", "name": "TSM ADR"},
    "usd_twd": {"symbol": "TWD=X", "name": "美元／台幣"},
}

_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_cache_lock = Lock()


def _chart_url(symbol: str, host: str = "query1.finance.yahoo.com") -> str:
    return f"https://{host}/v8/finance/chart/{quote(symbol, safe='')}"


def _cache_get(key: str, max_age: int = CACHE_TTL_SECONDS) -> dict[str, Any] | None:
    with _cache_lock:
        item = _cache.get(key)
    if not item:
        return None
    saved_at, value = item
    if time.time() - saved_at <= max_age:
        return dict(value)
    return None


def _cache_set(key: str, value: dict[str, Any]) -> None:
    with _cache_lock:
        _cache[key] = (time.time(), dict(value))


def _num(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(parse_number(value))
    except (ValueError, TypeError):
        return None


def _fetch_chart(symbol: str) -> dict[str, Any]:
    last_error: Exception | None = None
    for host in ("query1.finance.yahoo.com", "query2.finance.yahoo.com"):
        try:
            response = requests.get(
                _chart_url(symbol, host),
                params={"interval": "1m", "range": "1d"},
                headers=YAHOO_HEADERS,
                timeout=15,
            )
            response.raise_for_status()
            payload = response.json()
            chart = payload.get("chart", {})
            if chart.get("error"):
                raise ValueError(str(chart["error"]))
            results = chart.get("result") or []
            if not results:
                raise ValueError("Yahoo 回傳空白行情")
            return results[0]
        except Exception as error:
            last_error = error
    raise RuntimeError(f"Yahoo 行情查詢失敗：{last_error}")


def get_quote(key: str, force_refresh: bool = False) -> dict[str, Any]:
    spec = SYMBOLS[key]
    cache_key = f"quote:{key}"
    if not force_refresh:
        cached = _cache_get(cache_key)
        if cached:
            cached["cache"] = "fresh"
            return cached

    try:
        result = _fetch_chart(spec["symbol"])
        meta = result.get("meta", {})
        price = _num(meta.get("regularMarketPrice"))
        previous_close = _num(
            meta.get("chartPreviousClose", meta.get("previousClose"))
        )
        if price is None:
            closes = ((result.get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
            price = next((_num(v) for v in reversed(closes) if v is not None), None)
        if price is None or price <= 0:
            raise ValueError("找不到有效成交價")

        change = price - previous_close if previous_close not in (None, 0) else 0.0
        percent = change / previous_close * 100 if previous_close not in (None, 0) else 0.0
        market_time = meta.get("regularMarketTime")
        query_time = (
            datetime.fromtimestamp(market_time).strftime("%Y/%m/%d %H:%M:%S")
            if market_time
            else datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        )
        data = {
            "key": key,
            "symbol": spec["symbol"],
            "name": spec["name"],
            "price": price,
            "previousClose": previous_close,
            "change": change,
            "changePercent": percent,
            "queryTime": query_time,
            "source": "Yahoo Finance",
            "cache": "live",
        }
        _cache_set(cache_key, data)
        return data
    except Exception:
        stale = _cache_get(cache_key, STALE_CACHE_SECONDS)
        if stale:
            stale["cache"] = "stale"
            return stale
        raise


def get_taifex_quote() -> dict[str, Any]:
    cache_key = "quote:taifex"
    cached = _cache_get(cache_key)
    if cached:
        cached["cache"] = "fresh"
        return cached
    try:
        raw = get_market_data()
        data = {
            "key": "taifex",
            "symbol": raw.get("symbol", "WTX&"),
            "name": "台指期",
            "price": _num(raw.get("price")),
            "previousClose": _num(raw.get("previousClose")),
            "change": _num(raw.get("change")) or 0.0,
            "changePercent": _num(str(raw.get("changePercent", "0")).replace("%", "")) or 0.0,
            "queryTime": raw.get("queryTime"),
            "source": raw.get("source", "Yahoo"),
            "cache": "live",
        }
        if not data["price"]:
            raise ValueError("台指期價格無效")
        _cache_set(cache_key, data)
        return data
    except Exception:
        stale = _cache_get(cache_key, STALE_CACHE_SECONDS)
        if stale:
            stale["cache"] = "stale"
            return stale
        raise


def get_quotes(keys: list[str], include_taifex: bool = False) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    if include_taifex:
        try:
            output["taifex"] = get_taifex_quote()
        except Exception as error:
            output["taifex"] = {"name": "台指期", "error": str(error)}
    for key in keys:
        try:
            output[key] = get_quote(key)
        except Exception as error:
            output[key] = {"name": SYMBOLS[key]["name"], "error": str(error)}
    return output
