from fastapi import FastAPI, Header, Request

from bot.webhook import process_webhook
from services.yahoo import get_yahoo_taifex_data, test_yahoo_connection

app = FastAPI(title="LINE AI Assistant", version="4.0.1")


@app.get("/")
def home():
    return {
        "status": "LINE bot is running",
        "version": "V4.0.2 Risk Manager",
    }


@app.get("/test-yahoo")
def test_yahoo():
    return test_yahoo_connection()


@app.get("/test-market")
def test_market():
    return get_yahoo_taifex_data()


@app.post("/webhook")
async def webhook(request: Request, x_line_signature: str = Header(default="")):
    return await process_webhook(request, x_line_signature)
