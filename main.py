@app.post("/webhook")
async def webhook(request: Request, x_line_signature: str = Header(default="")):
    body = (await request.body()).decode("utf-8")

    print("=== WEBHOOK START ===")
    print("Signature:", x_line_signature)
    print("Body:", body)
    print("Secret exists:", bool(channel_secret))

    try:
        handler.handle(body, x_line_signature)
    except InvalidSignatureError as e:
        print("Invalid Signature:", e)
        raise HTTPException(status_code=400, detail="Invalid LINE signature")
    except Exception as e:
        print("Other Error:", e)
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "ok"}
