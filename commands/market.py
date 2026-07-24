from services.numbers import format_number, normalize_numeric_text, parse_number


def get_change_display(change_value) -> tuple[str, str, str]:
    try:
        numeric_change = parse_number(change_value)
    except (ValueError, TypeError):
        numeric_change = 0

    if numeric_change > 0:
        return "▲", format_number(abs(numeric_change)), "上漲"
    if numeric_change < 0:
        return "▼", format_number(abs(numeric_change)), "下跌"
    return "－", "0", "平盤"


def format_market_message(data: dict) -> str:
    if "error" in data:
        return f"⚠️ {data.get('error', '行情錯誤')}"

    change_icon, change_text, change_status = get_change_display(data.get("change", "0"))
    price = normalize_numeric_text(data.get("price"))
    open_price = normalize_numeric_text(data.get("open"))
    high = normalize_numeric_text(data.get("high"))
    low = normalize_numeric_text(data.get("low"))
    previous_close = normalize_numeric_text(data.get("previousClose", "無資料"))
    volume = normalize_numeric_text(data.get("volume"))
    best_bid = normalize_numeric_text(data.get("bestBid"))
    best_ask = normalize_numeric_text(data.get("bestAsk"))
    source = data.get("source", "未知")
    query_time = data.get("queryTime", "無資料")
    change_percent = data.get("changePercent", "無資料")

    if change_percent != "無資料" and not str(change_percent).endswith("%"):
        change_percent = f"{change_percent}%"

    if source == "Yahoo":
        source_message = "Yahoo 免費公開行情"
        warning_message = "⚠️ 免費行情可能有短暫延遲，請以交易平台報價為準。"
    else:
        source_message = "期交所每日行情備援"
        warning_message = (
            "⚠️ Yahoo 暫時無法使用，目前顯示期交所每日資料，並非即時成交價。"
        )

    message = (
        f"📈 {data.get('name', '台指期')}\n\n"
        f"💰 目前成交：{price}\n"
        f"📊 {change_status}：{change_icon}{change_text}\n"
        f"📉 漲跌幅：{change_percent}\n\n"
        f"開盤：{open_price}\n"
        f"最高：{high}\n"
        f"最低：{low}\n"
    )

    if previous_close != "無資料":
        message += f"昨收：{previous_close}\n"
    if volume != "無資料":
        message += f"總量：{volume}\n"
    if best_bid != "無資料":
        message += f"買價：{best_bid}\n"
    if best_ask != "無資料":
        message += f"賣價：{best_ask}\n"

    message += (
        f"\n🕒 資料時間：{query_time}\n"
        f"資料來源：{source_message}\n\n"
        f"{warning_message}"
    )
    return message
