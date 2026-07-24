from __future__ import annotations

from typing import Any

from services.numbers import parse_number


def calculate_change(price: Any, previous_close: Any) -> tuple[float, float]:
    """Return signed change and signed percent from price and previous close.

    The direction must always be decided by current price minus previous close,
    never by a scraped Yahoo change field that may lose its sign.
    """
    current = float(parse_number(price))
    previous = float(parse_number(previous_close))
    change = current - previous
    percent = change / previous * 100 if previous != 0 else 0.0
    return change, percent


def normalize_change_fields(data: dict[str, Any]) -> dict[str, Any]:
    """Copy data and overwrite change fields when price/previous close are valid."""
    normalized = dict(data)
    try:
        change, percent = calculate_change(
            normalized.get("price"), normalized.get("previousClose")
        )
    except (ValueError, TypeError):
        return normalized

    normalized["change"] = change
    normalized["changePercent"] = percent
    normalized["direction"] = "up" if change > 0 else "down" if change < 0 else "flat"
    return normalized
