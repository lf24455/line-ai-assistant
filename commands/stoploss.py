import re

from config import MICRO_TAIEX_VALUE_PER_POINT
from services.numbers import format_number, parse_number


def parse_stop_loss_command(user_text: str):
    pattern = r"^停損\s*(\d+(?:\.\d+)?)(?:\s*(\d+)\s*口)?$"
    match = re.match(pattern, user_text.strip())
    if not match:
        return None

    stop_points = float(match.group(1))
    contracts = int(match.group(2)) if match.group(2) else 1
    return stop_points, contracts


def format_stop_loss_message(data: dict, stop_points: float, contracts: int) -> str:
    current_price = parse_number(data.get("price", 0))
    if current_price <= 0:
        return "⚠️ 無法取得有效的台指期點數。"

    long_stop = current_price - stop_points
    short_stop = current_price + stop_points
    risk_per_contract = stop_points * MICRO_TAIEX_VALUE_PER_POINT
    total_risk = risk_per_contract * contracts
    source = data.get("source", "未知")
    query_time = data.get("queryTime", "無資料")

    if source == "Yahoo":
        source_text = "Yahoo 免費公開行情"
        warning_text = "⚠️ 免費行情可能有短暫延遲，實際停損請以交易平台報價為準。"
    else:
        source_text = "期交所每日行情備援"
        warning_text = "⚠️ Yahoo 暫時無法使用，本次使用每日行情試算，不是即時成交價。"

    return (
        "🧮 微型臺指停損試算\n\n"
        f"目前參考點數：{format_number(current_price)}\n"
        f"停損距離：{format_number(stop_points)} 點\n"
        f"口數：{contracts} 口\n\n"
        "📈 多單停損位置\n"
        f"{format_number(long_stop)}\n\n"
        "📉 空單停損位置\n"
        f"{format_number(short_stop)}\n\n"
        "💰 風險試算\n"
        f"每口風險：NT${format_number(risk_per_contract)}\n"
        f"總風險：NT${format_number(total_risk)}\n\n"
        "計算方式：\n"
        f"{format_number(stop_points)} 點 × NT$10 × {contracts} 口"
        f" = NT${format_number(total_risk)}\n\n"
        f"🕒 行情時間：{query_time}\n"
        f"資料來源：{source_text}\n\n"
        f"{warning_text}"
    )
