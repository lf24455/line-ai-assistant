import os

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")

YAHOO_URL = "https://tw.stock.yahoo.com/quote/WTX%26"
GAS_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbyO4D6oCx_z7xey-oHv8h2IXIA8US5_d_rqTzm5zTEFn5ntmMVKhd76sdDRu1LMvvuI"
    "/exec"
)

MICRO_TAIEX_VALUE_PER_POINT = 10

YAHOO_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/149.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}
