from services.taifex import get_taifex_daily_data
from services.yahoo import get_yahoo_taifex_data


def get_market_data() -> dict:
    try:
        yahoo_data = get_yahoo_taifex_data()
        print("Market source: Yahoo")
        return yahoo_data
    except Exception as yahoo_error:
        print("Yahoo market error:", repr(yahoo_error))

    try:
        taifex_data = get_taifex_daily_data()
        print("Market source: TAIFEX fallback")
        return taifex_data
    except Exception as taifex_error:
        print("TAIFEX fallback error:", repr(taifex_error))
        raise RuntimeError("Yahoo 與期交所備援皆無法取得行情。")
