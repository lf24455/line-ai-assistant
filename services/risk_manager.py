import math
import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FuturesProduct:
    name: str
    code: str
    point_value: int
    aliases: tuple[str, ...]


PRODUCTS: dict[str, FuturesProduct] = {
    "微台": FuturesProduct(
        name="微型臺指期貨",
        code="TMF",
        point_value=10,
        aliases=("微台", "微型台指", "微型臺指", "微型", "tmf"),
    ),
    "小台": FuturesProduct(
        name="小型臺指期貨",
        code="MTX",
        point_value=50,
        aliases=("小台", "小型台指", "小型臺指", "小型", "mtx"),
    ),
    "大台": FuturesProduct(
        name="臺股期貨",
        code="TX",
        point_value=200,
        aliases=("大台", "台指", "臺指", "台指期", "臺指期", "tx"),
    ),
}

DEFAULT_PRODUCT_KEY = "微台"


def _normalize(text: str) -> str:
    return (
        text.strip()
        .lower()
        .replace("，", " ")
        .replace(",", " ")
        .replace("：", ":")
        .replace("％", "%")
        .replace("點數", "點")
    )


def detect_product(text: str) -> tuple[str, FuturesProduct, bool]:
    normalized = _normalize(text)
    matches: list[tuple[int, str, FuturesProduct]] = []

    for key, product in PRODUCTS.items():
        for alias in product.aliases:
            position = normalized.find(alias.lower())
            if position >= 0:
                matches.append((position, key, product))

    if not matches:
        key = DEFAULT_PRODUCT_KEY
        return key, PRODUCTS[key], True

    # Prefer the earliest explicit product name in the sentence.
    _, key, product = sorted(matches, key=lambda item: item[0])[0]
    return key, product, False


def _parse_number_token(token: str) -> float:
    token = token.strip().replace(",", "")
    match = re.fullmatch(r"(\d+(?:\.\d+)?)(萬|千)?", token)
    if not match:
        raise ValueError("invalid number")

    value = float(match.group(1))
    unit = match.group(2)
    if unit == "萬":
        value *= 10000
    elif unit == "千":
        value *= 1000
    return value


def _extract_number_after_keyword(text: str, keyword: str, suffix: str = "") -> Optional[float]:
    normalized = _normalize(text)
    pattern = rf"{re.escape(keyword)}\s*([0-9][0-9,]*(?:\.[0-9]+)?(?:萬|千)?){suffix}"
    match = re.search(pattern, normalized)
    if not match:
        return None
    return _parse_number_token(match.group(1))


def _extract_contracts(text: str) -> int:
    normalized = _normalize(text)
    match = re.search(r"(\d+)\s*口", normalized)
    if match:
        return int(match.group(1))

    # Supports concise formats such as「停損50 10 小台」.
    number_tokens = re.findall(r"\d+(?:\.\d+)?", normalized)
    if len(number_tokens) >= 2 and "風險" not in normalized and "本金" not in normalized:
        return int(float(number_tokens[-1]))
    return 1


def parse_stop_loss_command(text: str) -> Optional[dict]:
    normalized = _normalize(text)
    if "停損" not in normalized and not re.search(r"\d+(?:\.\d+)?\s*點", normalized):
        return None
    if "風險" in normalized or "本金" in normalized:
        return None

    stop_points = _extract_number_after_keyword(normalized, "停損", r"\s*點?")
    if stop_points is None:
        point_match = re.search(r"(\d+(?:\.\d+)?)\s*點", normalized)
        if point_match:
            stop_points = float(point_match.group(1))
    if stop_points is None:
        return None

    product_key, product, used_default = detect_product(normalized)
    return {
        "type": "stop_loss",
        "stop_points": stop_points,
        "contracts": _extract_contracts(normalized),
        "product_key": product_key,
        "product": product,
        "used_default": used_default,
    }


def parse_risk_budget_command(text: str) -> Optional[dict]:
    normalized = _normalize(text)
    if "風險" not in normalized or "停損" not in normalized or "本金" in normalized:
        return None

    risk_budget = _extract_number_after_keyword(normalized, "風險")
    stop_points = _extract_number_after_keyword(normalized, "停損", r"\s*點?")
    if risk_budget is None or stop_points is None:
        return None

    product_key, product, used_default = detect_product(normalized)
    explicit_product = not used_default
    return {
        "type": "risk_budget",
        "risk_budget": risk_budget,
        "stop_points": stop_points,
        "product_key": product_key,
        "product": product,
        "explicit_product": explicit_product,
    }


def parse_capital_risk_command(text: str) -> Optional[dict]:
    normalized = _normalize(text)
    if "本金" not in normalized or "風險" not in normalized or "停損" not in normalized:
        return None

    capital = _extract_number_after_keyword(normalized, "本金")
    risk_match = re.search(r"風險\s*(\d+(?:\.\d+)?)\s*%", normalized)
    stop_points = _extract_number_after_keyword(normalized, "停損", r"\s*點?")
    if capital is None or not risk_match or stop_points is None:
        return None

    risk_percent = float(risk_match.group(1))
    product_key, product, used_default = detect_product(normalized)
    return {
        "type": "capital_risk",
        "capital": capital,
        "risk_percent": risk_percent,
        "risk_budget": capital * risk_percent / 100,
        "stop_points": stop_points,
        "product_key": product_key,
        "product": product,
        "explicit_product": not used_default,
    }


def calculate_stop_loss(stop_points: float, contracts: int, product: FuturesProduct) -> dict:
    risk_per_contract = stop_points * product.point_value
    return {
        "risk_per_contract": risk_per_contract,
        "total_risk": risk_per_contract * contracts,
    }


def calculate_position_size(risk_budget: float, stop_points: float, product: FuturesProduct) -> dict:
    risk_per_contract = stop_points * product.point_value
    max_contracts = math.floor(risk_budget / risk_per_contract) if risk_per_contract > 0 else 0
    actual_risk = max_contracts * risk_per_contract
    return {
        "risk_per_contract": risk_per_contract,
        "max_contracts": max_contracts,
        "actual_risk": actual_risk,
        "remaining_budget": risk_budget - actual_risk,
    }
