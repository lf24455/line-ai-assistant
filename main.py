import html
import os
import re
from datetime import datetime
from typing import Optional

import requests
from fastapi import FastAPI, Header, HTTPException, Request
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent


# =========================================================
# FastAPI
# =========================================================

app = FastAPI()


# =========================================================
# LINE 環境變數
# =========================================================

channel_secret = os.getenv(
    "LINE_CHANNEL_SECRET",
    "",
)

channel_access_token = os.getenv(
    "LINE_CHANNEL_ACCESS_TOKEN",
    "",
)

handler = WebhookHandler(channel_secret)


# =========================================================
# 行情來源
# =========================================================

YAHOO_URL = "https://tw.stock.yahoo.com/quote/WTX%26"

GAS_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbyO4D6oCx_z7xey-oHv8h2IXIA8US5_d_rqTzm5zTEFn5ntmMVKhd76sdDRu1LMvvuI"
    "/exec"
)


# 微型臺指每跳動 1 點，每口損益新臺幣 10 元
MICRO_TAIEX_VALUE_PER_POINT = 10


# =========================================================
# 共用 HTTP Header
# =========================================================

YAHOO_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/149.0.0.0 "
        "Safari/537.36"
    ),
    "Accept": (
        "text/html,"
        "application/xhtml+xml,"
        "application/xml;q=0.9,"
        "image/avif,"
        "image/webp,"
        "*/*;q=0.8"
    ),
    "Accept-Language": (
        "zh-TW,zh;q=0.9,"
        "en-US;q=0.8,en;q=0.7"
    ),
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


# =========================================================
# 首頁與測試網址
# =========================================================

@app.get("/")
def home():
    return {
        "status": "LINE bot is running",
        "version": "V3 Yahoo market data",
    }


@app.get("/test-yahoo")
def test_yahoo():
    """
    測試 Render 是否能連線 Yahoo。
    """
    response = requests.get(
        YAHOO_URL,
        headers=YAHOO_HEADERS,
        timeout=20,
    )

    response.raise_for_status()

    return {
        "status": response.status_code,
        "htmlLength": len(response.text),
        "preview": response.text[:200],
    }


@app.get("/test-market")
def test_market():
    """
    測試 Yahoo 行情解析結果。
    """
    return get_yahoo_taifex_data()


# =========================================================
# LINE Webhook
# =========================================================

@app.post("/webhook")
async def webhook(
    request: Request,
    x_line_signature: str = Header(default=""),
):
    body = (await request.body()).decode("utf-8")

    print("=== WEBHOOK START ===")
    print("Signature exists:", bool(x_line_signature))
    print("Secret exists:", bool(channel_secret))

    try:
        handler.handle(
            body,
            x_line_signature,
        )

    except InvalidSignatureError as error:
        print(
            "Invalid LINE signature:",
            repr(error),
        )

        raise HTTPException(
            status_code=400,
            detail="Invalid LINE signature",
        )

    except Exception as error:
        print(
            "Webhook error:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail="Webhook processing error",
        )

    return {
        "status": "ok",
    }


# =========================================================
# 數字處理
# =========================================================

def parse_number(value) -> float:
    text = (
        str(value)
        .strip()
        .replace(",", "")
        .replace("+", "")
        .replace("%", "")
    )

    if text in {
        "",
        "-",
        "--",
        "None",
        "null",
    }:
        raise ValueError(
            f"無法轉換成數字：{value}"
        )

    return float(text)


def format_number(value) -> str:
    number = float(value)

    if number.is_integer():
        return f"{int(number):,}"

    return f"{number:,.2f}"


def normalize_numeric_text(
    value: Optional[str],
) -> str:
    if value is None:
        return "無資料"

    text = str(value).strip()

    if not text:
        return "無資料"

    try:
        return format_number(
            parse_number(text)
        )

    except (ValueError, TypeError):
        return text


# =========================================================
# Yahoo HTML 整理
# =========================================================

def html_to_searchable_text(
    html_content: str,
) -> str:
    """
    移除 script、style、HTML 標籤，
    將網頁轉成方便搜尋的純文字。
    """

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

    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    text = html.unescape(text)

    text = (
        text
        .replace("\u3000", " ")
        .replace("\xa0", " ")
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def search_first(
    text: str,
    patterns: list[str],
) -> Optional[str]:
    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1).strip()

    return None


def extract_yahoo_number(
    text: str,
    label: str,
) -> Optional[str]:
    """
    從 Yahoo 純文字內容擷取指定欄位。

    例如：
    成交 44,377.00
    開盤 43,297.00
    """

    escaped_label = re.escape(label)

    patterns = [
        (
            rf"{escaped_label}\s*[:：]?\s*"
            rf"([+-]?\d[\d,]*(?:\.\d+)?)"
        ),
        (
            rf"{escaped_label}\s+"
            rf"([+-]?\d[\d,]*(?:\.\d+)?)"
        ),
    ]

    return search_first(
        text,
        patterns,
    )


def extract_yahoo_percent(
    text: str,
    label: str,
) -> Optional[str]:
    escaped_label = re.escape(label)

    patterns = [
        (
            rf"{escaped_label}\s*[:：]?\s*"
            rf"([+-]?\d[\d,]*(?:\.\d+)?%)"
        ),
    ]

    return search_first(
        text,
        patterns,
    )


def extract_yahoo_time(
    text: str,
) -> Optional[str]:
    patterns = [
        (
            r"資料時間\s*[:：]\s*"
            r"(\d{4}/\d{1,2}/\d{1,2}"
            r"\s+\d{1,2}:\d{2}(?::\d{2})?)"
        ),
        (
            r"(\d{4}/\d{1,2}/\d{1,2}"
            r"\s+\d{1,2}:\d{2}(?::\d{2})?)"
            r"\s*更新"
        ),
    ]

    return search_first(
        text,
        patterns,
    )


# =========================================================
# Yahoo 免費行情
# =========================================================

def get_yahoo_taifex_data() -> dict:
    response = requests.get(
        YAHOO_URL,
        headers=YAHOO_HEADERS,
        timeout=20,
    )

    print(
        "Yahoo status:",
        response.status_code,
    )

    print(
        "Yahoo HTML length:",
        len(response.text),
    )

    response.raise_for_status()

    searchable_text = html_to_searchable_text(
        response.text
    )

    print(
        "Yahoo text preview:",
        searchable_text[:1000],
    )

    price = extract_yahoo_number(
        searchable_text,
        "成交",
    )

    open_price = extract_yahoo_number(
        searchable_text,
        "開盤",
    )

    high = extract_yahoo_number(
        searchable_text,
        "最高",
    )

    low = extract_yahoo_number(
        searchable_text,
        "最低",
    )

    previous_close = extract_yahoo_number(
        searchable_text,
        "昨收",
    )

    change = extract_yahoo_number(
        searchable_text,
        "漲跌",
    )

    change_percent = extract_yahoo_percent(
        searchable_text,
        "漲跌幅",
    )

    volume = (
        extract_yahoo_number(
            searchable_text,
            "總量",
        )
        or extract_yahoo_number(
            searchable_text,
            "成交量",
        )
    )

    best_bid = extract_yahoo_number(
        searchable_text,
        "買價",
    )

    best_ask = extract_yahoo_number(
        searchable_text,
        "賣價",
    )

    open_interest = extract_yahoo_number(
        searchable_text,
        "未平倉",
    )

    data_time = extract_yahoo_time(
        searchable_text
    )

    if not price:
        raise ValueError(
            "Yahoo 頁面已取得，但找不到成交價。"
        )

    numeric_price = parse_number(price)

    if numeric_price <= 0:
        raise ValueError(
            "Yahoo 成交價不是有效數字。"
        )

    # 如果 Yahoo 未直接提供漲跌，
    # 使用成交價－昨收自行計算。
    if not change and previous_close:
        calculated_change = (
            numeric_price
            - parse_number(previous_close)
        )

        change = str(calculated_change)

    # 如果 Yahoo 未直接提供漲跌幅，
    # 使用漲跌／昨收自行計算。
    if (
        not change_percent
        and change
        and previous_close
    ):
        previous_close_number = parse_number(
            previous_close
        )

        if previous_close_number != 0:
            calculated_percent = (
                parse_number(change)
                / previous_close_number
                * 100
            )

            change_percent = (
                f"{calculated_percent:.2f}%"
            )

    if not data_time:
        data_time = datetime.now().strftime(
            "%Y/%m/%d %H:%M:%S"
        )

    data = {
        "name": "台指期近一",
        "symbol": "WTX&",
        "price": price,
        "change": change or "0",
        "changePercent": (
            change_percent or "無資料"
        ),
        "open": open_price or "無資料",
        "high": high or "無資料",
        "low": low or "無資料",
        "previousClose": (
            previous_close or "無資料"
        ),
        "volume": volume or "無資料",
        "bestBid": best_bid or "無資料",
        "bestAsk": best_ask or "無資料",
        "openInterest": (
            open_interest or "無資料"
        ),
        "queryTime": data_time,
        "source": "Yahoo",
        "isRealtime": True,
    }

    print(
        "Yahoo parsed data:",
        data,
    )

    return data


# =========================================================
# 期交所 GAS 備援資料
# =========================================================

def get_taifex_daily_data() -> dict:
    response = requests.get(
        GAS_URL,
        params={
            "q": "台指",
        },
        timeout=20,
    )

    print(
        "TAIFEX status:",
        response.status_code,
    )

    print(
        "TAIFEX response:",
        response.text[:1000],
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, dict):
        raise ValueError(
            "Apps Script 回傳格式不是 JSON 物件。"
        )

    data["source"] = "TAIFEX"
    data["isRealtime"] = False

    return data


# =========================================================
# 自動選擇行情來源
# =========================================================

def get_market_data() -> dict:
    """
    優先使用 Yahoo。
    Yahoo 發生錯誤時，改用 GAS／期交所每日行情。
    """

    try:
        yahoo_data = get_yahoo_taifex_data()

        print(
            "Market source: Yahoo"
        )

        return yahoo_data

    except Exception as yahoo_error:
        print(
            "Yahoo market error:",
            repr(yahoo_error),
        )

    try:
        taifex_data = get_taifex_daily_data()

        print(
            "Market source: TAIFEX fallback"
        )

        return taifex_data

    except Exception as taifex_error:
        print(
            "TAIFEX fallback error:",
            repr(taifex_error),
        )

        raise RuntimeError(
            "Yahoo 與期交所備援皆無法取得行情。"
        )


# =========================================================
# 漲跌格式
# =========================================================

def get_change_display(
    change_value,
) -> tuple[str, str, str]:
    try:
        numeric_change = parse_number(
            change_value
        )

    except (ValueError, TypeError):
        numeric_change = 0

    if numeric_change > 0:
        return (
            "▲",
            format_number(
                abs(numeric_change)
            ),
            "上漲",
        )

    if numeric_change < 0:
        return (
            "▼",
            format_number(
                abs(numeric_change)
            ),
            "下跌",
        )

    return (
        "－",
        "0",
        "平盤",
    )


# =========================================================
# 行情訊息
# =========================================================

def format_market_message(
    data: dict,
) -> str:
    if "error" in data:
        return (
            f"⚠️ {data.get('error', '行情錯誤')}"
        )

    change_icon, change_text, change_status = (
        get_change_display(
            data.get("change", "0")
        )
    )

    price = normalize_numeric_text(
        data.get("price")
    )

    open_price = normalize_numeric_text(
        data.get("open")
    )

    high = normalize_numeric_text(
        data.get("high")
    )

    low = normalize_numeric_text(
        data.get("low")
    )

    previous_close = normalize_numeric_text(
        data.get(
            "previousClose",
            "無資料",
        )
    )

    volume = normalize_numeric_text(
        data.get("volume")
    )

    best_bid = normalize_numeric_text(
        data.get("bestBid")
    )

    best_ask = normalize_numeric_text(
        data.get("bestAsk")
    )

    source = data.get(
        "source",
        "未知",
    )

    query_time = data.get(
        "queryTime",
        "無資料",
    )

    change_percent = data.get(
        "changePercent",
        "無資料",
    )

    if (
        change_percent != "無資料"
        and not str(change_percent).endswith("%")
    ):
        change_percent = (
            f"{change_percent}%"
        )

    if source == "Yahoo":
        source_message = (
            "Yahoo 免費公開行情"
        )

        warning_message = (
            "⚠️ 免費行情可能有短暫延遲，"
            "請以交易平台報價為準。"
        )

    else:
        source_message = (
            "期交所每日行情備援"
        )

        warning_message = (
            "⚠️ Yahoo 暫時無法使用，"
            "目前顯示期交所每日資料，"
            "並非即時成交價。"
        )

    message = (
        f"📈 {data.get('name', '台指期')}\n\n"
        f"💰 目前成交：{price}\n"
        f"📊 {change_status}："
        f"{change_icon}{change_text}\n"
        f"📉 漲跌幅：{change_percent}\n\n"
        f"開盤：{open_price}\n"
        f"最高：{high}\n"
        f"最低：{low}\n"
    )

    if previous_close != "無資料":
        message += (
            f"昨收：{previous_close}\n"
        )

    if volume != "無資料":
        message += (
            f"總量：{volume}\n"
        )

    if best_bid != "無資料":
        message += (
            f"買價：{best_bid}\n"
        )

    if best_ask != "無資料":
        message += (
            f"賣價：{best_ask}\n"
        )

    message += (
        f"\n🕒 資料時間：{query_time}\n"
        f"資料來源：{source_message}\n\n"
        f"{warning_message}"
    )

    return message


# =========================================================
# 停損指令
# =========================================================

def parse_stop_loss_command(
    user_text: str,
):
    """
    支援：

    停損50
    停損 50
    停損50 10口
    停損 50 10口
    """

    pattern = (
        r"^停損\s*(\d+(?:\.\d+)?)"
        r"(?:\s*(\d+)\s*口)?$"
    )

    match = re.match(
        pattern,
        user_text.strip(),
    )

    if not match:
        return None

    stop_points = float(
        match.group(1)
    )

    contracts = (
        int(match.group(2))
        if match.group(2)
        else 1
    )

    return (
        stop_points,
        contracts,
    )


# =========================================================
# 停損訊息
# =========================================================

def format_stop_loss_message(
    data: dict,
    stop_points: float,
    contracts: int,
) -> str:
    current_price = parse_number(
        data.get(
            "price",
            0,
        )
    )

    if current_price <= 0:
        return (
            "⚠️ 無法取得有效的台指期點數。"
        )

    long_stop = (
        current_price
        - stop_points
    )

    short_stop = (
        current_price
        + stop_points
    )

    risk_per_contract = (
        stop_points
        * MICRO_TAIEX_VALUE_PER_POINT
    )

    total_risk = (
        risk_per_contract
        * contracts
    )

    source = data.get(
        "source",
        "未知",
    )

    query_time = data.get(
        "queryTime",
        "無資料",
    )

    if source == "Yahoo":
        source_text = (
            "Yahoo 免費公開行情"
        )

        warning_text = (
            "⚠️ 免費行情可能有短暫延遲，"
            "實際停損請以交易平台報價為準。"
        )

    else:
        source_text = (
            "期交所每日行情備援"
        )

        warning_text = (
            "⚠️ Yahoo 暫時無法使用，"
            "本次使用每日行情試算，"
            "不是即時成交價。"
        )

    return (
        "🧮 微型臺指停損試算\n\n"
        f"目前參考點數："
        f"{format_number(current_price)}\n"
        f"停損距離："
        f"{format_number(stop_points)} 點\n"
        f"口數：{contracts} 口\n\n"
        "📈 多單停損位置\n"
        f"{format_number(long_stop)}\n\n"
        "📉 空單停損位置\n"
        f"{format_number(short_stop)}\n\n"
        "💰 風險試算\n"
        f"每口風險："
        f"NT${format_number(risk_per_contract)}\n"
        f"總風險："
        f"NT${format_number(total_risk)}\n\n"
        "計算方式：\n"
        f"{format_number(stop_points)} 點"
        f" × NT$10"
        f" × {contracts} 口"
        f" = NT${format_number(total_risk)}\n\n"
        f"🕒 行情時間：{query_time}\n"
        f"資料來源：{source_text}\n\n"
        f"{warning_text}"
    )


# =========================================================
# 指令說明
# =========================================================

def command_help() -> str:
    return (
        "🤖 目前可用指令\n\n"
        "📈 查詢台指行情\n"
        "台指\n"
        "台指期\n\n"
        "🧮 停損試算\n"
        "停損50\n"
        "停損50 10口\n\n"
        "例如：\n"
        "停損100 3口\n\n"
        "行情會優先使用 Yahoo，"
        "無法取得時自動切換期交所每日資料。"
    )


# =========================================================
# LINE 文字訊息處理
# =========================================================

@handler.add(
    MessageEvent,
    message=TextMessageContent,
)
def handle_text_message(event):
    user_text = (
        event.message.text.strip()
    )

    try:
        stop_loss_command = (
            parse_stop_loss_command(
                user_text
            )
        )

        if user_text in {
            "台指",
            "台指期",
        }:
            data = get_market_data()

            reply_text = (
                format_market_message(
                    data
                )
            )

        elif stop_loss_command:
            (
                stop_points,
                contracts,
            ) = stop_loss_command

            if stop_points <= 0:
                reply_text = (
                    "⚠️ 停損點數必須大於 0。"
                )

            elif contracts <= 0:
                reply_text = (
                    "⚠️ 口數必須大於 0。"
                )

            elif contracts > 1000:
                reply_text = (
                    "⚠️ 口數過大，請重新輸入。"
                )

            else:
                data = get_market_data()

                reply_text = (
                    format_stop_loss_message(
                        data=data,
                        stop_points=stop_points,
                        contracts=contracts,
                    )
                )

        elif user_text in {
            "說明",
            "功能",
            "指令",
            "help",
            "Help",
            "HELP",
        }:
            reply_text = command_help()

        else:
            reply_text = command_help()

    except requests.Timeout:
        reply_text = (
            "⚠️ 行情查詢逾時，請稍後再試。"
        )

    except requests.RequestException as error:
        print(
            "Market request error:",
            repr(error),
        )

        reply_text = (
            "⚠️ 無法連線到行情服務，"
            "請稍後再試。"
        )

    except (
        ValueError,
        TypeError,
        RuntimeError,
    ) as error:
        print(
            "Market data error:",
            repr(error),
        )

        reply_text = (
            "⚠️ 行情資料解析失敗，"
            "請稍後再試。"
        )

    except Exception as error:
        print(
            "Message handler error:",
            repr(error),
        )

        reply_text = (
            "⚠️ 執行指令時發生錯誤。"
        )

    configuration = Configuration(
        access_token=channel_access_token
    )

    with ApiClient(
        configuration
    ) as api_client:
        messaging_api = MessagingApi(
            api_client
        )

        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(
                        text=reply_text
                    )
                ],
            )
        )
