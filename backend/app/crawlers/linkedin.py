import re

from bs4 import BeautifulSoup

from app.crawlers.http import FetchError, http_fetch, looks_blocked
from app.crawlers.robots import allowed
from app.crawlers.types import CrawlResult, JobDraft

LISTING_URL = "https://www.linkedin.com/jobs/search?keywords=&location=Vietnam&position=1&pageNum=0"
SOURCE = "linkedin"


def parse_linkedin_html(html: str) -> list[JobDraft]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(".base-search-card, .job-search-card, li")
    drafts: list[JobDraft] = []
    for card in cards:
        title_node = card.select_one(".base-search-card__title, h3, .job-search-card__title")
        link = card.select_one("a.base-card__full-link, a[href*='/jobs/view/']")
        if title_node is None or link is None:
            continue
        href = str(link.get("href") or "").split("?")[0]
        title = title_node.get_text(" ", strip=True)
        if not title or "/jobs/view/" not in href:
            continue
        company_node = card.select_one(".base-search-card__subtitle, h4, .job-search-card__subtitle")
        location_node = card.select_one(".job-search-card__location, .base-search-card__metadata")
        id_match = re.search(r"(\d{6,})", href)
        drafts.append(
            JobDraft(
                source=SOURCE,
                external_id=id_match.group(1) if id_match else href,
                title=title,
                company=company_node.get_text(" ", strip=True) if company_node else "",
                location=location_node.get_text(" ", strip=True) if location_node else "Vietnam",
                url=href,
            )
        )
    return drafts


def collect_linkedin(fetch=http_fetch) -> CrawlResult:
    permitted, note = allowed(LISTING_URL, fetch=fetch)
    if not permitted:
        return CrawlResult(SOURCE, "blocked", note)
    try:
        status, body, _content_type = fetch(LISTING_URL)
    except FetchError as exc:
        return CrawlResult(SOURCE, "error", f"Không tải được LinkedIn: {exc}")
    if looks_blocked(status, body):
        return CrawlResult(SOURCE, "blocked", f"LinkedIn không mở trang public cho request này (HTTP {status}).")
    jobs = parse_linkedin_html(body)
    if not jobs:
        return CrawlResult(SOURCE, "empty", "LinkedIn không trả card việc làm public. Parser giữ nguyên, chờ HTML guest.")
    return CrawlResult(SOURCE, "ok", f"{note} Đọc {len(jobs)} tin public.", jobs)
