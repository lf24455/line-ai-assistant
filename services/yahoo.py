import html
import re
from datetime import datetime
from typing import Optional

import requests

from config import YAHOO_HEADERS, YAHOO_URL
from services.numbers import parse_number


def html_to_searchable_text(html_content: str) -> str:
    text = re.sub(
        r"<script\b[^>]*>.*?</script>",
        " ",
        html_content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    text = re.sub(
        r"<style\b[^>]*>.*?</style>",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    text = re.sub(
        r"<noscript\b[^>]*>.*?</noscript>",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = text.replace("\u3000", " ").replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def search_first(text: str, patterns: list[str]) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def extract_yahoo_number(text: str, label: str) -> Optional[str]:
    escaped_label = re.escape(label)
    patterns = [
        rf"{escaped_label}\s*[:：]?\s*([+-]?\d[\d,]*(?:\.\d+)?)",
        rf"{escaped_label}\s+([+-]?\d[\d,]*(?:\.\d+)?)",
    ]
    return search_first(text, patterns)


def extract_yahoo_percent(text: str, label: str) -> Optional[str]:
    escaped_label = re.escape(label)
    return search_first(
        text,
        [rf"{escaped_label}\s*[:：]?\s*([+-]?\d[\d,]*(?:\.\d+)?%)"],
    )


def extract_yahoo_time(text: str) -> Optional[str]:
    patterns = [
        r"資料時間\s*[:：]\s*(\d{4}/\d{1,2}/\d{1,2}\s+\d{1,2}:\d{2}(?::\d{2})?)",
        r"(\d{4}/\d{1,2}/\d{1,2}\s+\d{1,2}:\d{2}(?::\d{2})?)\s*更新",
    ]
    return search_first(text, patterns)


def test_yahoo_connection() -> dict:
    response = requests.get(YAHOO_URL, headers=YAHOO_HEADERS, timeout=20)
    response.raise_for_status()
    return {
        "status": response.status_code,
        "htmlLength": len(response.text),
        "preview": response.text[:200],
    }


def get_yahoo_taifex_data() -> dict:
    response = requests.get(YAHOO_URL, headers=YAHOO_HEADERS, timeout=20)
    print("Yahoo status:", response.status_code)
    print("Yahoo HTML length:", len(response.text))
    response.raise_for_status()

    searchable_text = html_to_searchable_text(response.text)
    print("Yahoo text preview:", searchable_text[:1000])

    price = extract_yahoo_number(searchable_text, "成交")
    open_price = extract_yahoo_number(searchable_text, "開盤")
    high = extract_yahoo_number(searchable_text, "最高")
    low = extract_yahoo_number(searchable_text, "最低")
    previous_close = extract_yahoo_number(searchable_text, "昨收")
    change = extract_yahoo_number(searchable_text, "漲跌")
    change_percent = extract_yahoo_percent(searchable_text, "漲跌幅")
    volume = (
        extract_yahoo_number(searchable_text, "總量")
        or extract_yahoo_number(searchable_text, "成交量")
    )
    best_bid = extract_yahoo_number(searchable_text, "買價")
    best_ask = extract_yahoo_number(searchable_text, "賣價")
    open_interest = extract_yahoo_number(searchable_text, "未平倉")
    data_time = extract_yahoo_time(searchable_text)

    if not price:
        raise ValueError("Yahoo 頁面已取得，但找不到成交價。")

    numeric_price = parse_number(price)
    if numeric_price <= 0:
        raise ValueError("Yahoo 成交價不是有效數字。")

    # 優先使用成交價與昨收重新計算，避免 Yahoo 頁面的漲跌符號解析錯誤
if previous_close:
    previous_close_number = parse_number(previous_close)

    if previous_close_number > 0:
        calculated_change = numeric_price - previous_close_number
        calculated_percent = calculated_change / previous_close_number * 100

        change = f"{calculated_change:.0f}"
        change_percent = f"{calculated_percent:+.2f}%"

    if not data_time:
        data_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
numeric_change = parse_number(change or "0")

if numeric_change > 0:
    direction = "up"
elif numeric_change < 0:
    direction = "down"
else:
    direction = "flat"
    data = {
        "name": "台指期近一",
        "symbol": "WTX&",
        "price": price,
        "change": change or "0",
        "changePercent": change_percent or "無資料",
        "open": open_price or "無資料",
        "high": high or "無資料",
        "low": low or "無資料",
        "previousClose": previous_close or "無資料",
        "volume": volume or "無資料",
        "bestBid": best_bid or "無資料",
        "bestAsk": best_ask or "無資料",
        "openInterest": open_interest or "無資料",
        "queryTime": data_time,
        "source": "Yahoo",
        "isRealtime": True,
    }
    print("Yahoo parsed data:", data)
    return data
