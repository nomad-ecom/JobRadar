from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from app.crawlers.http import USER_AGENT, FetchError, http_fetch


def allowed(url: str, fetch=http_fetch) -> tuple[bool, str]:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        status, body, content_type = fetch(robots_url)
    except FetchError as exc:
        return True, f"Không đọc được robots.txt ({exc}). Vẫn thử trang public."
    if status >= 400 or "html" in content_type.lower() or body.lstrip().startswith("<"):
        return True, "Nguồn không công bố robots.txt. Chỉ đọc trang public."
    parser = RobotFileParser()
    parser.parse(body.splitlines())
    if parser.can_fetch(USER_AGENT, url):
        return True, "robots.txt cho phép URL này."
    return False, "robots.txt không cho phép URL này. Bỏ qua."
