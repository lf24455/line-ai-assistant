import requests

from commands.help import command_help
from commands.market import format_market_message
from commands.stoploss import (
    format_capital_risk_message,
    format_risk_budget_message,
    format_stop_loss_message,
    parse_capital_risk_command,
    parse_risk_budget_command,
    parse_stop_loss_command,
)
from services.market import get_market_data


def _validate_common(command: dict) -> str | None:
    stop_points = command.get("stop_points", 0)
    if stop_points <= 0:
        return "⚠️ 停損點數必須大於 0。"
    if stop_points > 10000:
        return "⚠️ 停損點數過大，請重新輸入。"
    return None


def route_text_command(user_text: str) -> str:
    try:
        user_text = user_text.strip()

        if user_text in {"台指", "台指期"}:
            return format_market_message(get_market_data())

        capital_command = parse_capital_risk_command(user_text)
        if capital_command:
            validation = _validate_common(capital_command)
            if validation:
                return validation
            if capital_command["capital"] <= 0:
                return "⚠️ 本金必須大於 0。"
            if not 0 < capital_command["risk_percent"] <= 100:
                return "⚠️ 風險比例必須介於 0% 到 100%。"
            return format_capital_risk_message(capital_command)

        risk_command = parse_risk_budget_command(user_text)
        if risk_command:
            validation = _validate_common(risk_command)
            if validation:
                return validation
            if risk_command["risk_budget"] <= 0:
                return "⚠️ 最大風險必須大於 0。"
            return format_risk_budget_message(risk_command)

        stop_loss_command = parse_stop_loss_command(user_text)
        if stop_loss_command:
            validation = _validate_common(stop_loss_command)
            if validation:
                return validation
            contracts = stop_loss_command["contracts"]
            if contracts <= 0:
                return "⚠️ 口數必須大於 0。"
            if contracts > 1000:
                return "⚠️ 口數過大，請重新輸入。"
            return format_stop_loss_message(get_market_data(), stop_loss_command)

        if "停損" in user_text or "風險" in user_text or "本金" in user_text:
            return (
                "⚠️ 指令格式無法辨識。\n\n"
                "可輸入：\n"
                "停損50 10口 小台\n"
                "風險3000 停損50 小台\n"
                "本金20萬 風險2% 停損50 小台"
            )

        return command_help()

    except requests.Timeout:
        return "⚠️ 行情查詢逾時，請稍後再試。"
    except requests.RequestException as error:
        print("Market request error:", repr(error))
        return "⚠️ 無法連線到行情服務，請稍後再試。"
    except (ValueError, TypeError, RuntimeError) as error:
        print("Market data error:", repr(error))
        return "⚠️ 資料解析失敗，請稍後再試。"
    except Exception as error:
        print("Message handler error:", repr(error))
        return "⚠️ 執行指令時發生錯誤。"
