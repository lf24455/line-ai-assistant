from typing import Optional


def parse_number(value) -> float:
    text = (
        str(value)
        .strip()
        .replace(",", "")
        .replace("+", "")
        .replace("%", "")
    )

    if text in {"", "-", "--", "None", "null"}:
        raise ValueError(f"無法轉換成數字：{value}")

    return float(text)


def format_number(value) -> str:
    number = float(value)
    if number.is_integer():
        return f"{int(number):,}"
    return f"{number:,.2f}"


def normalize_numeric_text(value: Optional[str]) -> str:
    if value is None:
        return "無資料"

    text = str(value).strip()
    if not text:
        return "無資料"

    try:
        return format_number(parse_number(text))
    except (ValueError, TypeError):
        return text
