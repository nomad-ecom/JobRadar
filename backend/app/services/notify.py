from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Job, Match, Notification, Preference, User, utcnow

FREQUENCIES = {"instant": timedelta(0), "daily": timedelta(hours=20), "weekly": timedelta(days=6)}


def _job_line(job: Job, score: int) -> str:
    salary = job.salary_text or "lương chưa rõ"
    return f"- {score} điểm | {job.title} | {job.company} | {job.location} | {salary}\n  {job.url}"


def _send_resend(settings: Settings, to_email: str, subject: str, text: str, html: str) -> None:
    response = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {settings.resend_api_key}"},
        json={"from": settings.email_from, "to": [to_email], "subject": subject, "text": text, "html": html},
        timeout=20,
    )
    response.raise_for_status()


def _due(preference: Preference, now: datetime) -> bool:
    window = FREQUENCIES.get(preference.frequency, timedelta(0))
    if preference.frequency == "instant" or preference.last_digest_at is None or window == timedelta(0):
        return True
    last = preference.last_digest_at
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return now - last >= window


def notify_user(db: Session, settings: Settings, user: User, preference: Preference) -> Notification | None:
    if not preference.email_enabled:
        return None
    now = utcnow()
    if not _due(preference, now):
        return None
    pending = db.scalars(
        select(Match)
        .where(Match.user_id == user.id, Match.notified_at.is_(None), Match.score >= preference.min_score)
        .order_by(Match.score.desc())
    ).all()
    if not pending:
        return None
    jobs = {job.id: job for job in db.scalars(select(Job).where(Job.id.in_([item.job_id for item in pending]))).all()}
    lines = []
    for item in pending:
        job = jobs.get(item.job_id)
        if job is None:
            continue
        lines.append(_job_line(job, item.score))
    if not lines:
        return None
    subject = f"JobRadar: {len(lines)} việc từ {preference.min_score} điểm"
    text = "Có việc mới khớp với hồ sơ của bạn:\n\n" + "\n".join(lines)
    note = Notification(
        user_id=user.id,
        subject=subject,
        body=text,
        status="queued",
        match_ids=[item.id for item in pending],
    )
    db.add(note)
    db.flush()
    pixel = ""
    if settings.public_api_url:
        pixel = f'<img src="{settings.public_api_url.rstrip("/")}/notifications/{note.id}/open.gif" alt="" width="1" height="1"/>'
    html = "<p>Có việc mới khớp với hồ sơ của bạn.</p><pre>" + "\n".join(lines) + "</pre>" + pixel
    if settings.email_configured:
        try:
            _send_resend(settings, user.email, subject, text, html)
            note.status = "sent"
            note.sent_at = now
        except httpx.HTTPError as exc:
            note.status = "failed"
            note.body = text + f"\n\nGửi email lỗi: {exc}"
    else:
        note.status = "logged"
        note.sent_at = now
    for item in pending:
        item.notified_at = now
    if preference.frequency != "instant":
        preference.last_digest_at = now
    else:
        preference.last_digest_at = now
    return note
