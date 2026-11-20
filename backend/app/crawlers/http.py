import httpx

USER_AGENT = "JobRadarBot/1.0 (+https://github.com/nomad-ecom/JobRadar)"

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "vi,en;q=0.8",
}


class FetchError(Exception):
    pass


def http_fetch(url: str, timeout: float = 20) -> tuple[int, str, str]:
    """Return status, body, and content-type. Raises FetchError on transport failure."""
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, headers=HEADERS) as client:
            response = client.get(url)
    except httpx.HTTPError as exc:
        raise FetchError(str(exc)) from exc
    content_type = response.headers.get("content-type", "")
    return response.status_code, response.text, content_type


def looks_blocked(status: int, body: str) -> bool:
    if status in {401, 403, 429, 503, 999}:
        return True
    sample = body[:4000].lower()
    markers = (
        "attention required",
        "just a moment",
        "cf-browser-verification",
        "you have been blocked",
        "access denied",
        "authwall",
    )
    return any(marker in sample for marker in markers)
