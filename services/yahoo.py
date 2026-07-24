import html
import re
from datetime import datetime
from typing import Optional

import requests

from config import YAHOO_HEADERS, YAHOO_URL
from services.market_math import calculate_change
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
    # Yahoo HTML 的漲跌欄位有時會遺失負號，因此只讀成交價與昨收後自行計算。
    volume = (
        extract_yahoo_number(searchable_text, "總量")
        or extract_yahoo_number(searchable_text, "成交量")
    )
    best_ask = extract_yahoo_number(searchable_text, "賣價")
    open_interest = extract_yahoo_number(searchable_text, "未平倉")
    data_time = extract_yahoo_time(searchable_text)

    if not price:
        raise ValueError("Yahoo 頁面已取得，但找不到成交價。")

    numeric_price = parse_number(price)
    if numeric_price <= 0:
        raise ValueError("Yahoo 成交價不是有效數字。")

    change = 0.0
    change_percent = 0.0
    if previous_close:
        change, change_percent = calculate_change(price, previous_close)

    if not data_time:
        data_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    data = {
        "name": "台指期近一",
        "symbol": "WTX&",
        "price": price,
        "change": change,
        "changePercent": change_percent,
        "open": open_price or "無資料",
        "high": high or "無資料",
        "low": low or "無資料",
        "previousClose": previous_close or "無資料",
        "volume": volume or "無資料",
        "bestAsk": best_ask or "無資料",
        "openInterest": open_interest or "無資料",
        "queryTime": data_time,
        "source": "Yahoo",
        "isRealtime": True,
    }
    print("Yahoo parsed data:", data)
    return data
