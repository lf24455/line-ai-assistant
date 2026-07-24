from __future__ import annotations

from typing import Any

from services.global_market import get_quote, get_quotes


def _price(value: Any) -> str:
    try:
        number = float(value)
    except (ValueError, TypeError):
        return "無資料"
    decimals = 4 if number < 100 else 2
    text = f"{number:,.{decimals}f}"
    return text.rstrip("0").rstrip(".")


def _line(data: dict[str, Any]) -> str:
    name = data.get("name", "行情")
    if data.get("error"):
        return f"{name}\n暫時無法取得"
    change = float(data.get("change") or 0)
    percent = float(data.get("changePercent") or 0)
    icon = "▲" if change > 0 else "▼" if change < 0 else "－"
    sign_change = abs(change)
    return f"{name}\n{_price(data.get('price'))} {icon}{_price(sign_change)} ({percent:+.2f}%)"


def _footer(data: dict[str, dict[str, Any]]) -> str:
    stale = any(item.get("cache") == "stale" for item in data.values())
    text = "\n\n⚠️ 免費行情可能延遲，請以交易平台為準。"
    if stale:
        text += "\n部分資料使用最近一次成功快取。"
    return text


def format_market_summary() -> str:
    data = get_quotes(
        ["taiex", "tsmc", "0050", "dow", "sp500", "nasdaq", "sox", "tsm_adr", "usd_twd"],
        include_taifex=True,
    )
    message = (
        "🌏 全球市場\n"
        "━━━━━━━━━━━━━━\n\n"
        "🇹🇼 台灣\n\n"
        f"{_line(data['taifex'])}\n\n"
        f"{_line(data['taiex'])}\n\n"
        f"{_line(data['tsmc'])}\n\n"
        f"{_line(data['0050'])}\n\n"
        "━━━━━━━━━━━━━━\n\n"
        "🇺🇸 美國\n\n"
        f"{_line(data['dow'])}\n\n"
        f"{_line(data['sp500'])}\n\n"
        f"{_line(data['nasdaq'])}\n\n"
        f"{_line(data['sox'])}\n\n"
        f"{_line(data['tsm_adr'])}\n\n"
        "━━━━━━━━━━━━━━\n\n"
        "💵 匯率\n\n"
        f"{_line(data['usd_twd'])}"
    )
    return message + _footer(data)


def format_tw_market() -> str:
    data = get_quotes(["taiex", "tsmc", "0050"], include_taifex=True)
    message = (
        "🇹🇼 台股市場\n"
        "━━━━━━━━━━━━━━\n\n"
        f"{_line(data['taifex'])}\n\n"
        f"{_line(data['taiex'])}\n\n"
        f"{_line(data['tsmc'])}\n\n"
        f"{_line(data['0050'])}"
    )
    return message + _footer(data)


def format_us_market() -> str:
    data = get_quotes(["dow", "sp500", "nasdaq", "sox", "tsm_adr"])
    message = (
        "🇺🇸 美股市場\n"
        "━━━━━━━━━━━━━━\n\n"
        f"{_line(data['dow'])}\n\n"
        f"{_line(data['sp500'])}\n\n"
        f"{_line(data['nasdaq'])}\n\n"
        f"{_line(data['sox'])}\n\n"
        f"{_line(data['tsm_adr'])}"
    )
    return message + _footer(data)


def format_etf_market() -> str:
    data = get_quotes(["0050", "0056", "00919", "00940"])
    message = (
        "📦 台灣 ETF\n"
        "━━━━━━━━━━━━━━\n\n"
        f"{_line(data['0050'])}\n\n"
        f"{_line(data['0056'])}\n\n"
        f"{_line(data['00919'])}\n\n"
        f"{_line(data['00940'])}"
    )
    return message + _footer(data)


def format_single_quote(key: str) -> str:
    data = get_quote(key)
    return f"🔎 即時行情\n━━━━━━━━━━━━━━\n\n{_line(data)}" + _footer({key: data})
