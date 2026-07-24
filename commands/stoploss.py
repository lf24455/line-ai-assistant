from services.numbers import format_number, parse_number
from services.risk_manager import (
    PRODUCTS,
    FuturesProduct,
    calculate_position_size,
    calculate_stop_loss,
    parse_capital_risk_command,
    parse_risk_budget_command,
    parse_stop_loss_command,
)


def _market_source_text(data: dict) -> tuple[str, str]:
    source = data.get("source", "未知")
    if source == "Yahoo":
        return (
            "Yahoo 免費公開行情",
            "⚠️ 免費行情可能有短暫延遲，實際停損請以交易平台報價為準。",
        )
    return (
        "期交所每日行情備援",
        "⚠️ Yahoo 暫時無法使用，本次使用每日行情試算，不是即時成交價。",
    )


def format_stop_loss_message(data: dict, command: dict) -> str:
    current_price = parse_number(data.get("price", 0))
    if current_price <= 0:
        return "⚠️ 無法取得有效的台指期點數。"

    stop_points = command["stop_points"]
    contracts = command["contracts"]
    product: FuturesProduct = command["product"]
    result = calculate_stop_loss(stop_points, contracts, product)
    long_stop = current_price - stop_points
    short_stop = current_price + stop_points
    source_text, warning_text = _market_source_text(data)
    default_note = (
        "\n💡 未指定商品，已使用「微台」作為預設。"
        if command.get("used_default")
        else ""
    )

    return (
        "📊 停損試算\n\n"
        f"商品：{command['product_key']}（{product.code}）\n"
        f"1 點：NT${format_number(product.point_value)}\n"
        f"目前參考點數：{format_number(current_price)}\n"
        f"停損距離：{format_number(stop_points)} 點\n"
        f"口數：{contracts} 口\n\n"
        "📈 多單停損位置\n"
        f"{format_number(long_stop)}\n\n"
        "📉 空單停損位置\n"
        f"{format_number(short_stop)}\n\n"
        "💰 風險試算\n"
        f"每口風險：NT${format_number(result['risk_per_contract'])}\n"
        f"總風險：NT${format_number(result['total_risk'])}\n\n"
        "計算方式：\n"
        f"{format_number(stop_points)} 點 × NT${format_number(product.point_value)}"
        f" × {contracts} 口 = NT${format_number(result['total_risk'])}\n\n"
        f"🕒 行情時間：{data.get('queryTime', '無資料')}\n"
        f"資料來源：{source_text}"
        f"{default_note}\n\n"
        f"{warning_text}"
    )


def _format_one_product_position(risk_budget: float, stop_points: float, key: str) -> str:
    product = PRODUCTS[key]
    result = calculate_position_size(risk_budget, stop_points, product)
    return (
        f"{key}（{product.code}）：{result['max_contracts']} 口"
        f"｜實際風險 NT${format_number(result['actual_risk'])}"
    )


def format_risk_budget_message(command: dict) -> str:
    risk_budget = command["risk_budget"]
    stop_points = command["stop_points"]

    if command["explicit_product"]:
        key = command["product_key"]
        product: FuturesProduct = command["product"]
        result = calculate_position_size(risk_budget, stop_points, product)
        return (
            "🛡️ 建議口數\n\n"
            f"商品：{key}（{product.code}）\n"
            f"最大風險：NT${format_number(risk_budget)}\n"
            f"停損距離：{format_number(stop_points)} 點\n"
            f"每口風險：NT${format_number(result['risk_per_contract'])}\n\n"
            f"建議最多：{result['max_contracts']} 口\n"
            f"實際風險：NT${format_number(result['actual_risk'])}\n"
            f"剩餘額度：NT${format_number(result['remaining_budget'])}\n\n"
            "⚠️ 這是數學試算，不含手續費、交易稅與滑價。"
        )

    product_lines = "\n".join(
        _format_one_product_position(risk_budget, stop_points, key)
        for key in ("微台", "小台", "大台")
    )
    return (
        "🛡️ 建議口數\n\n"
        f"最大風險：NT${format_number(risk_budget)}\n"
        f"停損距離：{format_number(stop_points)} 點\n\n"
        f"{product_lines}\n\n"
        "⚠️ 這是數學試算，不含手續費、交易稅與滑價。"
    )


def format_capital_risk_message(command: dict) -> str:
    product: FuturesProduct = command["product"]
    result = calculate_position_size(
        command["risk_budget"], command["stop_points"], product
    )

    if command["explicit_product"]:
        detail = (
            f"商品：{command['product_key']}（{product.code}）\n"
            f"每口風險：NT${format_number(result['risk_per_contract'])}\n\n"
            f"建議最多：{result['max_contracts']} 口\n"
            f"實際風險：NT${format_number(result['actual_risk'])}\n"
            f"剩餘額度：NT${format_number(result['remaining_budget'])}"
        )
    else:
        detail = "\n".join(
            _format_one_product_position(
                command["risk_budget"], command["stop_points"], key
            )
            for key in ("微台", "小台", "大台")
        )

    return (
        "💼 本金風控\n\n"
        f"本金：NT${format_number(command['capital'])}\n"
        f"單筆風險：{format_number(command['risk_percent'])}%\n"
        f"最大可承受虧損：NT${format_number(command['risk_budget'])}\n"
        f"停損距離：{format_number(command['stop_points'])} 點\n\n"
        f"{detail}\n\n"
        "⚠️ 這是數學試算，不含手續費、交易稅與滑價。"
    )


__all__ = [
    "parse_stop_loss_command",
    "parse_risk_budget_command",
    "parse_capital_risk_command",
    "format_stop_loss_message",
    "format_risk_budget_message",
    "format_capital_risk_message",
]
