from datetime import datetime
import requests

import os

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

channel_secret = os.getenv("LINE_CHANNEL_SECRET", "")
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
SHEET_API_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbzjFS9NuaGZaagTVAdltf1o2jPr3qbDAXUX9GQGq7ajkWM6QWFaw6k3SFp0SqQFQfbO"
    "/exec"
)

handler = WebhookHandler(channel_secret)


@app.get("/")
def home():
    return {"status": "LINE bot is running"}


@app.post("/webhook")
async def webhook(
    request: Request,
    x_line_signature: str = Header(default=""),
):
    body = (await request.body()).decode("utf-8")

    print("=== WEBHOOK START ===")
    print("Signature exists:", bool(x_line_signature))
    print("Body:", body)
    print("Secret exists:", bool(channel_secret))

    try:
        handler.handle(body, x_line_signature)

    except InvalidSignatureError as error:
        print("Invalid Signature:", error)
        raise HTTPException(
            status_code=400,
            detail="Invalid LINE signature",
        )

    except Exception as error:
        print("Other Error:", repr(error))
        raise HTTPException(
            status_code=500,
            detail="Webhook processing error",
        )

    return {"status": "ok"}


def get_taifex_message() -> str:
    """
    第一版先確認機器人能連到期交所 OpenAPI。
    下一步再依實際資料欄位挑出 TX 近月契約。
    """
    api_url = "https://openapi.taifex.com.tw/v1/DailyMarketReportFut"

    try:
        response = requests.get(api_url, timeout=15)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list) or not data:
            return "⚠️ 目前沒有取得台指期資料，請稍後再試。"

        return (
            "📈 台指期資料來源已連線\n\n"
            f"取得資料筆數：{len(data)} 筆\n"
            f"查詢時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            "下一步會自動篩選 TX 近月契約與目前點數。"
        )

    except requests.RequestException as error:
        print("TAIFEX API request error:", repr(error))
        return "⚠️ 無法連接期交所資料，請稍後再試。"

    except ValueError as error:
        print("TAIFEX JSON error:", repr(error))
        return "⚠️ 期交所回傳格式異常，請稍後再試。"



def get_sheet_market_data() -> str:
    try:
        response = requests.get(SHEET_API_URL, timeout=15)
        response.raise_for_status()

        result = response.text.strip()

        if not result:
            return "⚠️ Google Sheet 目前沒有回傳資料。"

        return result

    except requests.RequestException as error:
        print("Google Apps Script error:", repr(error))
        return "⚠️ 暫時無法讀取行情資料，請稍後再試。"
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    user_text = event.message.text.strip()

    if user_text in {"台指", "台指期", "全部", "行情"}:
        reply_text = get_sheet_market_data()
    else:
        reply_text = (
            "目前可用指令：\n"
            "• 台指\n"
            "• 台指期\n"
            "• 全部\n"
            "• 行情"
        )

    configuration = Configuration(
        access_token=channel_access_token
    )

    with ApiClient(configuration) as api_client:
        messaging_api = MessagingApi(api_client)

        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)],
            )
        )
