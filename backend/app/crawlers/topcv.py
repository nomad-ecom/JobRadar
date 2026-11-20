import re

from bs4 import BeautifulSoup

from app.crawlers.http import FetchError, http_fetch, looks_blocked
from app.crawlers.robots import allowed
from app.crawlers.types import CrawlResult, JobDraft
from app.services.salary import parse_salary

LISTING_URL = "https://www.topcv.vn/tim-viec"
SOURCE = "topcv"


def parse_topcv_html(html: str) -> list[JobDraft]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(".job-item-search-result, .job-item")
    drafts: list[JobDraft] = []
    for card in cards:
        title_node = card.select_one("h3 a, .title a, a[href*='/viec-lam/'], a[href*='/brand/']")
        if title_node is None:
            continue
        title = title_node.get_text(" ", strip=True)
        href = str(title_node.get("href") or "")
        if href.startswith("/"):
            href = "https://www.topcv.vn" + href
        if not title or "/viec-lam" not in href and "/brand/" not in href and "topcv.vn" not in href:
            continue
        company_node = card.select_one("a.company, .company-name, .company")
        location_node = card.select_one(".city-text, .address, label.address, .location")
        salary_node = card.select_one(".label-salary, .salary")
        salary_text = salary_node.get_text(" ", strip=True) if salary_node else ""
        salary_min, salary_max, currency = parse_salary(salary_text)
        id_match = re.search(r"(\d{4,})", href)
        drafts.append(
            JobDraft(
                source=SOURCE,
                external_id=id_match.group(1) if id_match else href,
                title=title,
                company=company_node.get_text(" ", strip=True) if company_node else "",
                location=location_node.get_text(" ", strip=True) if location_node else "",
                url=href,
                salary_text=salary_text,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency=currency,
            )
        )
    return drafts


def collect_topcv(fetch=http_fetch) -> CrawlResult:
    permitted, note = allowed(LISTING_URL, fetch=fetch)
    if not permitted:
        return CrawlResult(SOURCE, "blocked", note)
    try:
        status, body, _content_type = fetch(LISTING_URL)
    except FetchError as exc:
        return CrawlResult(SOURCE, "error", f"Không tải được TopCV: {exc}")
    if looks_blocked(status, body):
        return CrawlResult(SOURCE, "blocked", f"TopCV chặn request tự động (HTTP {status}). Không vượt Cloudflare.")
    jobs = parse_topcv_html(body)
    if not jobs:
        return CrawlResult(SOURCE, "empty", "TopCV trả HTML nhưng không thấy card việc làm. Cần cập nhật selector.")
    return CrawlResult(SOURCE, "ok", f"{note} Đọc {len(jobs)} card trên trang public.", jobs)
