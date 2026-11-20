import hashlib
import re
import unicodedata


def fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value or "")
    stripped = "".join(
        char for char in unicodedata.normalize("NFD", normalized.lower()) if unicodedata.category(char) != "Mn"
    )
    stripped = stripped.replace("đ", "d")
    return re.sub(r"\s+", " ", stripped).strip()


def tokens(value: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9+#]+", fold(value)) if len(token) > 1]


def dedup_hash(title: str, company: str, location: str) -> str:
    raw = "|".join([fold(title), fold(company), fold(location)])
    return hashlib.sha256(raw.encode()).hexdigest()


def unique_keep(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        cleaned = re.sub(r"\s+", " ", item).strip(" ,;|/-")
        if not cleaned:
            continue
        key = fold(cleaned)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(cleaned)
    return ordered
