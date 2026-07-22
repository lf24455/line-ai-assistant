import os
import re

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


app = FastAPI()


# =========================
# LINE 環境變數
# =========================

channel_secret = os.getenv(
    "LINE_CHANNEL_SECRET",
    "",
)

channel_access_token = os.getenv(
    "LINE_CHANNEL_ACCESS_TOKEN",
    "",
)


# =========================
# Google Apps Script
# =========================

GAS_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbyO4D6oCx_z7xey-oHv8h2IXIA8US5_d_rqTzm5zTEFn5ntmMVKhd76sdDRu1LMvvuI"
    "/exec"
)


handler = WebhookHandler(channel_secret)


# 微型臺指每跳動 1 點
# 每口損益為新臺幣 10 元
MICRO_TAIEX_VALUE_PER_POINT = 10


# =========================
# 首頁
# =========================

@app.get("/")
def home():
    return {
        "status": "LINE bot is running",
    }


# =========================
# Yahoo 測試網址
# =========================

@app.get("/test-yahoo")
def test_yahoo():
    return get_yahoo_taifex_data()


# =========================
# LINE Webhook
# =========================

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
            "Invalid Signature:",
            error,
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


# =========================
# Yahoo 台指期頁面測試
# =========================

def get_yahoo_taifex_data() -> dict:
    url = "https://tw.stock.yahoo.com/quote/WTX%26"

    response = requests.get(
        url,
        timeout=20,
        headers={
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
        },
    )

    print(
        "Yahoo status:",
        response.status_code,
    )

    print(
        "Yahoo HTML length:",
        len(response.text),
    )

    print(
        "Yahoo preview:",
        response.text[:500],
    )

    response.raise_for_status()

    return {
        "status": response.status_code,
        "htmlLength": len(response.text),
        "preview": response.text[:200],
    }


# =========================
# 取得期交所每日行情
# =========================

def get_taifex_data() -> dict:
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
        response.text,
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, dict):
        raise ValueError(
            "Apps Script 回傳格式不是 JSON 物件"
        )

    print(
        "TAIFEX JSON:",
        data,
    )

    return data


# =========================
# 數字處理
# =========================

def parse_number(value) -> float:
    text = (
        str(value)
        .strip()
        .replace(",", "")
    )

    return float(text)


def format_number(value: float) -> str:
    if float(value).is_integer():
        return f"{int(value):,}"

    return f"{value:,.2f}"


# =========================
# 台指訊息格式
# =========================

def format_taifex_message(
    data: dict,
) -> str:
    if "error" in data:
        detail = data.get("detail")
        preview = data.get("preview")

        message = (
            f"⚠️ {data['error']}"
        )

        if detail:
            message += (
                f"\n詳細資訊：{detail}"
            )

        if preview:
            message += (
                f"\n回傳內容：{preview}"
            )

        return message

    change = str(
        data.get(
            "change",
            "0",
        )
    ).strip()

    try:
        numeric_change = parse_number(
            change
        )

    except (
        ValueError,
        TypeError,
    ):
        numeric_change = 0

    if numeric_change > 0:
        change_icon = "▲"
        change_text = change.lstrip("+")

    elif numeric_change < 0:
        change_icon = "▼"
        change_text = change.lstrip("-")

    else:
        change_icon = "－"
        change_text = "0"

    trading_date = str(
        data.get(
            "tradingDate",
            "無資料",
        )
    )

    if (
        len(trading_date) == 8
        and trading_date.isdigit()
    ):
        trading_date = (
            f"{trading_date[:4]}/"
            f"{trading_date[4:6]}/"
            f"{trading_date[6:]}"
        )

    return (
        f"📈 {data.get('name', '台指期')}\n\n"

        f"📅 近月契約："
        f"{data.get('contract', '無資料')}\n"

        f"💰 收盤點數："
        f"{data.get('price', '無資料')}\n"

        f"📊 漲跌："
        f"{change_icon}{change_text}\n"

        f"📉 漲跌幅："
        f"{data.get('changePercent', '無資料')}\n\n"

        f"開盤："
        f"{data.get('open', '無資料')}\n"

        f"最高："
        f"{data.get('high', '無資料')}\n"

        f"最低："
        f"{data.get('low', '無資料')}\n"

        f"結算價："
        f"{data.get('settlementPrice', '無資料')}\n"

        f"成交量："
        f"{data.get('volume', '無資料')}\n"

        f"未平倉量："
        f"{data.get('openInterest', '無資料')}\n"

        f"最佳買價："
        f"{data.get('bestBid', '無資料')}\n"

        f"最佳賣價："
        f"{data.get('bestAsk', '無資料')}\n\n"

        f"交易時段："
        f"{data.get('session', '無資料')}\n"

        f"資料日期："
        f"{trading_date}\n"

        f"查詢時間："
        f"{data.get('queryTime', '無資料')}\n\n"

        "⚠️ 此為期交所每日行情資料，"
        "非逐筆即時報價。"
    )


# =========================
# 停損指令解析
# =========================

def parse_stop_loss_command(
    user_text: str,
):
    """
    支援格式：

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


# =========================
# 停損訊息格式
# =========================

def format_stop_loss_message(
    data: dict,
    stop_points: float,
    contracts: int,
) -> str:
    if "error" in data:
        return (
            f"⚠️ {data['error']}"
        )

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

    return (
        "🧮 微型臺指停損試算\n\n"

        f"目前參考點數："
        f"{format_number(current_price)}\n"

        f"停損距離："
        f"{format_number(stop_points)} 點\n"

        f"口數："
        f"{contracts} 口\n\n"

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

        "⚠️ 目前點數取自期交所每日行情，"
        "不是逐筆即時成交價。"
    )


# =========================
# 指令說明
# =========================

def command_help() -> str:
    return (
        "🤖 目前可用指令\n\n"

        "📈 查詢行情\n"
        "台指\n"
        "台指期\n\n"

        "🧮 停損試算\n"
        "停損50\n"
        "停損50 10口\n\n"

        "例如輸入：\n"
        "停損100 3口"
    )


# =========================
# LINE 文字訊息處理
# =========================

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
            data = get_taifex_data()

            print(
                "TAIFEX data:",
                data,
            )

            reply_text = (
                format_taifex_message(
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
                data = get_taifex_data()

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
        }:
            reply_text = command_help()

        else:
            reply_text = command_help()

    except requests.Timeout:
        reply_text = (
            "⚠️ 行情查詢逾時，"
            "請稍後再試。"
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
    ) as error:
        print(
            "Data format error:",
            repr(error),
        )

        reply_text = (
            "⚠️ 行情資料格式異常，"
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
