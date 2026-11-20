import re

from app.textutil import fold

_MULTIPLIERS = {
    "ty": 1_000_000_000,
    "trieu": 1_000_000,
    "tr": 1_000_000,
    "k": 1_000,
    "nghin": 1_000,
}


def _number(raw: str) -> float:
    cleaned = raw.strip().replace(" ", "")
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        parts = cleaned.split(",")
        cleaned = cleaned.replace(",", "") if len(parts[-1]) == 3 else cleaned.replace(",", ".")
    return float(cleaned)


def parse_salary(text: str) -> tuple[int | None, int | None, str]:
    """Return min, max, and currency. Missing bounds stay None."""
    folded = fold(text or "")
    if not folded or any(word in folded for word in ("thuong luong", "negotiable", "competitive")):
        return None, None, "VND"

    currency = "USD" if any(mark in folded for mark in ("usd", "$", "dollar")) else "VND"
    numbers = re.findall(r"\d+(?:[.,]\d+)?", folded)
    if not numbers:
        return None, None, currency

    unit = 1
    for name, multiplier in _MULTIPLIERS.items():
        if re.search(rf"(?:^| ){name}(?: |$)", folded):
            unit = multiplier
            break
    if currency == "USD" and unit == 1:
        unit = 1

    values = [int(round(_number(number) * unit)) for number in numbers[:2]]
    if len(values) == 1:
        if re.search(r"\b(tu|from|tren|over)\b", folded):
            return values[0], None, currency
        if re.search(r"\b(toi|den|upto|up to|under|duoi)\b", folded):
            return None, values[0], currency
        return values[0], values[0], currency
    low, high = sorted(values[:2])
    return low, high, currency
