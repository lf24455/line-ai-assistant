from fastapi import Header, HTTPException, Request
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from commands.router import route_text_command
from config import LINE_CHANNEL_SECRET
from bot.reply import reply_text

handler = WebhookHandler(LINE_CHANNEL_SECRET)


async def process_webhook(request: Request, x_line_signature: str = Header(default="")):
    body = (await request.body()).decode("utf-8")
    print("=== WEBHOOK START ===")
    print("Signature exists:", bool(x_line_signature))
    print("Secret exists:", bool(LINE_CHANNEL_SECRET))

    try:
        handler.handle(body, x_line_signature)
    except InvalidSignatureError as error:
        print("Invalid LINE signature:", repr(error))
        raise HTTPException(status_code=400, detail="Invalid LINE signature")
    except Exception as error:
        print("Webhook error:", repr(error))
        raise HTTPException(status_code=500, detail="Webhook processing error")

    return {"status": "ok"}


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    user_text = event.message.text.strip()
    reply_text(event.reply_token, route_text_command(user_text))
