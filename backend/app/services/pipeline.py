from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.crawlers.http import http_fetch
from app.crawlers.registry import COLLECTORS, sources_for
from app.crawlers.types import CrawlResult, JobDraft
from app.models import CrawlRun, Job, Match, Preference, Profile, User, utcnow
from app.services.matching import score_job
from app.services.notify import notify_user
from app.textutil import dedup_hash


def _retry_with_browser(collector, previous: CrawlResult) -> CrawlResult:
    try:
        from app.crawlers.browser import playwright_fetch

        rendered = collector(fetch=playwright_fetch)
    except Exception as exc:
        previous.message += f" Playwright không chạy: {exc}"
        return previous
    if rendered.jobs:
        rendered.message = "Playwright đọc được trang public. " + rendered.message
        return rendered
    previous.message += " Playwright cũng không lấy được tin, không vượt captcha."
    return previous


def upsert_jobs(db: Session, drafts: list[JobDraft]) -> tuple[int, int]:
    created = 0
    seen: dict[str, Job] = {}
    for draft in drafts:
        if not draft.title:
            continue
        digest = dedup_hash(draft.title, draft.company, draft.location)
        existing = seen.get(digest) or db.scalar(select(Job).where(Job.dedup_hash == digest))
        if existing is None:
            job = Job(
                source=draft.source,
                external_id=draft.external_id,
                dedup_hash=digest,
                title=draft.title,
                company=draft.company,
                location=draft.location,
                salary_text=draft.salary_text,
                salary_min=draft.salary_min,
                salary_max=draft.salary_max,
                salary_currency=draft.salary_currency,
                description=draft.description,
                url=draft.url,
                skills=draft.skills,
                posted_at=draft.posted_at,
                crawled_at=utcnow(),
            )
            db.add(job)
            seen[digest] = job
            created += 1
            continue
        existing.source = draft.source
        existing.external_id = draft.external_id or existing.external_id
        existing.salary_text = draft.salary_text or existing.salary_text
        existing.salary_min = draft.salary_min if draft.salary_min is not None else existing.salary_min
        existing.salary_max = draft.salary_max if draft.salary_max is not None else existing.salary_max
        existing.description = draft.description or existing.description
        existing.url = draft.url or existing.url
        existing.skills = draft.skills or existing.skills
        existing.crawled_at = utcnow()
        seen[digest] = existing
    return len(drafts), created


def match_users(db: Session) -> int:
    users = db.scalars(select(User)).all()
    created = 0
    for user in users:
        profile = db.get(Profile, user.id)
        preference = db.get(Preference, user.id)
        if profile is None or not (profile.desired_title or profile.skills):
            continue
        allowed = set((preference.sources if preference else []) or [])
        jobs = db.scalars(select(Job)).all()
        for job in jobs:
            if allowed and job.source not in allowed:
                continue
            scored = score_job(profile, job)
            current = db.scalar(select(Match).where(Match.user_id == user.id, Match.job_id == job.id))
            if current is None:
                db.add(
                    Match(
                        user_id=user.id,
                        job_id=job.id,
                        score=scored["score"],
                        breakdown=scored,
                    )
                )
                created += 1
            else:
                current.score = scored["score"]
                current.breakdown = scored
    return created


def crawl_and_match(db: Session, settings: Settings | None = None, fetch=None) -> list[CrawlRun]:
    settings = settings or get_settings()
    if fetch is None:
        fetch = http_fetch
    runs: list[CrawlRun] = []
    for source in sources_for(settings):
        collector = COLLECTORS[source]
        started = utcnow()
        try:
            if source == "sample":
                result: CrawlResult = collector()
            else:
                result = collector(fetch=fetch)
                if settings.playwright and result.status in {"blocked", "empty"}:
                    result = _retry_with_browser(collector, result)
        except Exception as exc:
            result = CrawlResult(source, "error", f"Crawler lỗi: {exc}")
        found, created = upsert_jobs(db, result.jobs)
        run = CrawlRun(
            source=source,
            status=result.status,
            jobs_found=found,
            jobs_new=created,
            message=result.message,
            started_at=started,
            finished_at=utcnow(),
        )
        db.add(run)
        runs.append(run)
    db.flush()
    match_users(db)
    db.flush()
    for user in db.scalars(select(User)).all():
        preference = db.get(Preference, user.id)
        if preference is not None:
            notify_user(db, settings, user, preference)
    db.commit()
    return runs
