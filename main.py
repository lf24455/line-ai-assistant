import os

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

channel_secret = os.getenv("LINE_CHANNEL_SECRET", "")
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")

# 這裡使用你目前新版的 Apps Script API
GAS_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbxKbeEYsS2OtTPSKcfTnDibFS5KWFpuSI33b2Mi8Bkc96TAoeMjjuyhXgTmc8WwBk-W"
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
        print("Webhook error:", repr(error))
        raise HTTPException(
            status_code=500,
            detail="Webhook processing error",
        )

    return {"status": "ok"}


def get_taifex_data() -> dict:
    response = requests.get(
        GAS_URL,
        params={"q": "台指"},
        timeout=20,
    )
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, dict):
        raise ValueError("Apps Script 回傳格式不是 JSON 物件")

    return data


def format_taifex_message(data: dict) -> str:
    if "error" in data:
        detail = data.get("detail")

        if detail:
            return (
                f"⚠️ {data['error']}\n"
                f"詳細資訊：{detail}"
            )

        return f"⚠️ {data['error']}"

    change = str(data.get("change", "0")).strip()
    change_value = change.lstrip("+-")

    try:
        numeric_change = float(change.replace(",", ""))
    except ValueError:
        numeric_change = 0

    if numeric_change > 0:
        change_icon = "▲"
    elif numeric_change < 0:
        change_icon = "▼"
    else:
        change_icon = "－"

    trading_date = str(
        data.get("tradingDate", "無資料")
    )

    # 將 20260721 顯示成 2026/07/21
    if len(trading_date) == 8 and trading_date.isdigit():
        trading_date = (
            f"{trading_date[:4]}/"
            f"{trading_date[4:6]}/"
            f"{trading_date[6:]}"
        )

    return (
        f"📈 {data.get('name', '台指期')}\n\n"
        f"近月契約：{data.get('contract', '無資料')}\n"
        f"收盤點數：{data.get('price', '無資料')}\n"
        f"漲跌：{change_icon}{change_value}\n"
        f"漲跌幅：{data.get('changePercent', '無資料')}\n"
        f"最高：{data.get('high', '無資料')}\n"
        f"最低：{data.get('low', '無資料')}\n"
        f"成交量：{data.get('volume', '無資料')}\n"
        f"交易時段：{data.get('session', '無資料')}\n"
        f"資料日期：{trading_date}\n"
        f"查詢時間：{data.get('queryTime', '無資料')}\n\n"
        "⚠️ 此為期交所每日行情資料，非逐筆即時報價。"
    )


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    user_text = event.message.text.strip()

    try:
        if user_text in {"台指", "台指期"}:
            data = get_taifex_data()
            print(data)
            reply_text = format_taifex_message(data)

        else:
            reply_text = (
                "目前可用指令：\n"
                "• 台指\n"
                "• 台指期"
            )

    except requests.Timeout as error:
        print("Apps Script timeout:", repr(error))
        reply_text = "⚠️ 行情查詢逾時，請稍後再試。"

    except requests.RequestException as error:
        print("Apps Script request error:", repr(error))
        reply_text = "⚠️ 暫時無法取得台指資料，請稍後再試。"

    except ValueError as error:
        print("Apps Script JSON error:", repr(error))
        reply_text = "⚠️ 行情資料格式異常，請稍後再試。"

    except Exception as error:
        print("Message handler error:", repr(error))
        reply_text = "⚠️ 系統處理訊息時發生錯誤。"

    configuration = Configuration(
        access_token=channel_access_token
    )

    with ApiClient(configuration) as api_client:
        messaging_api = MessagingApi(api_client)

        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(text=reply_text)
                ],
            )
        )
