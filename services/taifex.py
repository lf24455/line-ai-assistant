import requests

from config import GAS_URL


def get_taifex_daily_data() -> dict:
    response = requests.get(GAS_URL, params={"q": "台指"}, timeout=20)
    print("TAIFEX status:", response.status_code)
    print("TAIFEX response:", response.text[:1000])
    response.raise_for_status()

    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("Apps Script 回傳格式不是 JSON 物件。")

    data["source"] = "TAIFEX"
    data["isRealtime"] = False
    return data
