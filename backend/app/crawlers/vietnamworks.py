import json
import re

from app.crawlers.http import FetchError, http_fetch, looks_blocked
from app.crawlers.robots import allowed
from app.crawlers.types import CrawlResult, JobDraft
from app.services.salary import parse_salary

LISTING_URL = "https://www.vietnamworks.com/tim-viec-lam/tim-tat-ca-viec-lam"
SOURCE = "vietnamworks"


def parse_vietnamworks_html(html: str) -> list[JobDraft]:
    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not match:
        return []
    payload = json.loads(match.group(1))
    raw_jobs = payload.get("props", {}).get("pageProps", {}).get("outstandingJobs") or []
    drafts: list[JobDraft] = []
    for item in raw_jobs:
        if not isinstance(item, dict) or not item.get("jobTitle"):
            continue
        url = str(item.get("url") or "").split("?")[0]
        id_match = re.search(r"(\d{5,})", url)
        company = "Công ty ẩn danh" if item.get("isAnonymous") else str(item.get("company") or "")
        salary_text = str(item.get("prettySalary") or item.get("salary") or "")
        salary_min, salary_max, currency = parse_salary(salary_text)
        drafts.append(
            JobDraft(
                source=SOURCE,
                external_id=id_match.group(1) if id_match else url,
                title=str(item["jobTitle"]).strip(),
                company=company.strip(),
                location=str(item.get("location") or "").strip(),
                url=url,
                description=str(item.get("jobDescription") or ""),
                salary_text=salary_text,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency=currency,
                skills=[str(skill) for skill in item.get("skills") or [] if skill],
            )
        )
    return drafts


def collect_vietnamworks(fetch=http_fetch) -> CrawlResult:
    permitted, note = allowed(LISTING_URL, fetch=fetch)
    if not permitted:
        return CrawlResult(SOURCE, "blocked", note)
    try:
        status, body, _content_type = fetch(LISTING_URL)
    except FetchError as exc:
        return CrawlResult(SOURCE, "error", f"Không tải được VietnamWorks: {exc}")
    if looks_blocked(status, body):
        return CrawlResult(SOURCE, "blocked", f"VietnamWorks trả về trang chặn (HTTP {status}). Không vượt captcha.")
    try:
        jobs = parse_vietnamworks_html(body)
    except (json.JSONDecodeError, TypeError, KeyError) as exc:
        return CrawlResult(SOURCE, "error", f"HTML VietnamWorks đổi cấu trúc: {exc}")
    if not jobs:
        return CrawlResult(SOURCE, "empty", "Trang public không còn khối outstandingJobs. Cần cập nhật parser.")
    return CrawlResult(
        SOURCE,
        "ok",
        f"{note} Lấy {len(jobs)} tin nổi bật nhúng trong HTML public, không phải toàn bộ kết quả tìm kiếm.",
        jobs,
    )
