import requests

from commands.help import command_help
from commands.market import format_market_message
from commands.stoploss import format_stop_loss_message, parse_stop_loss_command
from services.market import get_market_data


def route_text_command(user_text: str) -> str:
    try:
        stop_loss_command = parse_stop_loss_command(user_text)

        if user_text in {"台指", "台指期"}:
            return format_market_message(get_market_data())

        if stop_loss_command:
            stop_points, contracts = stop_loss_command
            if stop_points <= 0:
                return "⚠️ 停損點數必須大於 0。"
            if contracts <= 0:
                return "⚠️ 口數必須大於 0。"
            if contracts > 1000:
                return "⚠️ 口數過大，請重新輸入。"

            return format_stop_loss_message(
                data=get_market_data(),
                stop_points=stop_points,
                contracts=contracts,
            )

        return command_help()

    except requests.Timeout:
        return "⚠️ 行情查詢逾時，請稍後再試。"
    except requests.RequestException as error:
        print("Market request error:", repr(error))
        return "⚠️ 無法連線到行情服務，請稍後再試。"
    except (ValueError, TypeError, RuntimeError) as error:
        print("Market data error:", repr(error))
        return "⚠️ 行情資料解析失敗，請稍後再試。"
    except Exception as error:
        print("Message handler error:", repr(error))
        return "⚠️ 執行指令時發生錯誤。"
