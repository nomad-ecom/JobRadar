from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.crawlers.registry import COLLECTORS, sources_for
from app.db import get_db
from app.deps import get_current_user
from app.models import CrawlRun, Job, Match, Notification, Preference, Profile, User, utcnow
from app.schemas import (
    AuthOut,
    CrawlRunOut,
    LoginIn,
    MatchOut,
    MatchUpdate,
    NotificationOut,
    PreferenceIn,
    PreferenceOut,
    ProfileIn,
    ProfileOut,
    RegisterIn,
    StatsOut,
    UserOut,
)
from app.security import create_token, hash_password, verify_password
from app.services.cv_parser import extract_pdf_text, parse_cv_text
from app.services.pipeline import crawl_and_match
from app.services.storage import save_cv

router = APIRouter()
STATUSES = {"new", "viewed", "saved", "applied"}
FREQUENCIES = {"instant", "daily", "weekly"}
PIXEL = __import__("base64").b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")


def _user_out(user: User) -> UserOut:
    return UserOut(id=user.id, email=user.email, name=user.name)


def _profile_out(profile: Profile) -> ProfileOut:
    return ProfileOut(
        desired_title=profile.desired_title,
        summary=profile.summary,
        skills=list(profile.skills or []),
        experience_years=profile.experience_years,
        locations=list(profile.locations or []),
        salary_min=profile.salary_min,
        salary_max=profile.salary_max,
        salary_currency=profile.salary_currency,
        cv_path=profile.cv_path,
        updated_at=profile.updated_at,
    )


def _preference_out(preference: Preference) -> PreferenceOut:
    return PreferenceOut(
        min_score=preference.min_score,
        frequency=preference.frequency,
        sources=list(preference.sources or []),
        email_enabled=preference.email_enabled,
        last_digest_at=preference.last_digest_at,
    )


def _job_out(job: Job):
    from app.schemas import JobOut

    return JobOut(
        id=job.id,
        source=job.source,
        title=job.title,
        company=job.company,
        location=job.location,
        salary_text=job.salary_text,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
        description=job.description,
        url=job.url,
        skills=list(job.skills or []),
        crawled_at=job.crawled_at,
    )


def _match_out(match: Match, job: Job) -> MatchOut:
    return MatchOut(
        id=match.id,
        score=match.score,
        status=match.status,
        breakdown=match.breakdown or {},
        notified_at=match.notified_at,
        created_at=match.created_at,
        job=_job_out(job),
    )


@router.get("/health")
def health() -> dict:
    return {"ok": True, "service": "jobradar"}


@router.post("/auth/register", response_model=AuthOut)
def register(body: RegisterIn, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> AuthOut:
    user = User(email=str(body.email).lower(), name=body.name.strip(), password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email đã được đăng ký") from exc
    db.add(Preference(user_id=user.id, sources=sources_for(settings)))
    db.commit()
    return AuthOut(access_token=create_token(user.id, settings.secret), user=_user_out(user))


@router.post("/auth/login", response_model=AuthOut)
def login(body: LoginIn, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> AuthOut:
    user = db.scalar(select(User).where(User.email == str(body.email).lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu chưa đúng")
    return AuthOut(access_token=create_token(user.id, settings.secret), user=_user_out(user))


@router.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return _user_out(user)


@router.get("/profile", response_model=ProfileOut)
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProfileOut:
    profile = db.get(Profile, user.id)
    if profile is None:
        return ProfileOut()
    return _profile_out(profile)


@router.put("/profile", response_model=ProfileOut)
def update_profile(body: ProfileIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProfileOut:
    profile = db.get(Profile, user.id)
    if profile is None:
        profile = Profile(user_id=user.id)
        db.add(profile)
    profile.desired_title = body.desired_title.strip()
    profile.summary = body.summary.strip()
    profile.skills = [skill.strip() for skill in body.skills if skill.strip()]
    profile.experience_years = body.experience_years
    profile.locations = [item.strip() for item in body.locations if item.strip()]
    profile.salary_min = body.salary_min
    profile.salary_max = body.salary_max
    profile.salary_currency = body.salary_currency.upper()[:8] or "VND"
    profile.updated_at = utcnow()
    db.commit()
    return _profile_out(profile)


@router.post("/profile/cv", response_model=ProfileOut)
def upload_cv(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ProfileOut:
    filename = (file.filename or "").lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Chỉ nhận file PDF")
    data = file.file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File lớn hơn 5MB")
    if not data.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="File không phải PDF hợp lệ")
    try:
        text = extract_pdf_text(data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Không đọc được PDF: {exc}") from exc
    parsed = parse_cv_text(text)
    if not text.strip():
        parsed["summary"] = "Không đọc được chữ trong PDF. File có thể là ảnh scan. Hãy nhập tay các trường bên dưới."
    path = save_cv(settings, user.id, file.filename or "cv.pdf", data)
    profile = db.get(Profile, user.id)
    if profile is None:
        profile = Profile(user_id=user.id)
        db.add(profile)
    for key, value in parsed.items():
        setattr(profile, key, value)
    profile.cv_path = path
    profile.updated_at = utcnow()
    db.commit()
    return _profile_out(profile)


@router.get("/preferences", response_model=PreferenceOut)
def get_preferences(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PreferenceOut:
    preference = db.get(Preference, user.id)
    if preference is None:
        raise HTTPException(status_code=404, detail="Chưa có cài đặt")
    return _preference_out(preference)


@router.put("/preferences", response_model=PreferenceOut)
def update_preferences(
    body: PreferenceIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PreferenceOut:
    if body.frequency not in FREQUENCIES:
        raise HTTPException(status_code=400, detail="Tần suất chỉ nhận instant, daily hoặc weekly")
    unknown = [source for source in body.sources if source not in COLLECTORS]
    if unknown:
        raise HTTPException(status_code=400, detail="Nguồn không hỗ trợ: " + ", ".join(unknown))
    preference = db.get(Preference, user.id)
    if preference is None:
        preference = Preference(user_id=user.id)
        db.add(preference)
    preference.min_score = body.min_score
    preference.frequency = body.frequency
    preference.sources = body.sources
    preference.email_enabled = body.email_enabled
    db.commit()
    return _preference_out(preference)


@router.get("/matches", response_model=list[MatchOut])
def list_matches(
    status: str | None = None,
    min_score: int | None = Query(default=None, ge=0, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MatchOut]:
    if status is not None and status not in STATUSES:
        raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ")
    statement = select(Match, Job).join(Job, Job.id == Match.job_id).where(Match.user_id == user.id)
    if status:
        statement = statement.where(Match.status == status)
    if min_score is not None:
        statement = statement.where(Match.score >= min_score)
    rows = db.execute(statement.order_by(Match.score.desc(), Match.created_at.desc()).limit(100)).all()
    return [_match_out(match, job) for match, job in rows]


@router.get("/matches/stats", response_model=StatsOut)
def match_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> StatsOut:
    rows = db.scalars(select(Match).where(Match.user_id == user.id)).all()
    opened = db.scalar(
        select(func.count()).select_from(Notification).where(Notification.user_id == user.id, Notification.opened_at.is_not(None))
    )
    return StatsOut(
        total=len(rows),
        high=sum(1 for row in rows if row.score >= 70),
        new=sum(1 for row in rows if row.status == "new"),
        saved=sum(1 for row in rows if row.status == "saved"),
        applied=sum(1 for row in rows if row.status == "applied"),
        notified=sum(1 for row in rows if row.notified_at is not None),
        opened_notifications=int(opened or 0),
    )


@router.get("/matches/{match_id}", response_model=MatchOut)
def get_match(match_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MatchOut:
    match = db.get(Match, match_id)
    if match is None or match.user_id != user.id:
        raise HTTPException(status_code=404, detail="Không thấy việc này")
    if match.status == "new":
        match.status = "viewed"
        match.updated_at = utcnow()
        db.commit()
    job = db.get(Job, match.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Tin tuyển dụng đã bị gỡ")
    return _match_out(match, job)


@router.patch("/matches/{match_id}", response_model=MatchOut)
def update_match(
    match_id: str,
    body: MatchUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MatchOut:
    if body.status not in STATUSES:
        raise HTTPException(status_code=400, detail="Trạng thái chỉ nhận new, viewed, saved hoặc applied")
    match = db.get(Match, match_id)
    if match is None or match.user_id != user.id:
        raise HTTPException(status_code=404, detail="Không thấy việc này")
    match.status = body.status
    match.updated_at = utcnow()
    db.commit()
    job = db.get(Job, match.job_id)
    return _match_out(match, job)


@router.post("/crawl", response_model=list[CrawlRunOut])
def crawl_now(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[CrawlRunOut]:
    del user
    runs = crawl_and_match(db)
    return [
        CrawlRunOut(
            id=run.id,
            source=run.source,
            status=run.status,
            jobs_found=run.jobs_found,
            jobs_new=run.jobs_new,
            message=run.message,
            started_at=run.started_at,
            finished_at=run.finished_at,
        )
        for run in runs
    ]


@router.get("/crawl/runs", response_model=list[CrawlRunOut])
def crawl_runs(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[CrawlRunOut]:
    del user
    runs = db.scalars(select(CrawlRun).order_by(CrawlRun.started_at.desc()).limit(30)).all()
    return [
        CrawlRunOut(
            id=run.id,
            source=run.source,
            status=run.status,
            jobs_found=run.jobs_found,
            jobs_new=run.jobs_new,
            message=run.message,
            started_at=run.started_at,
            finished_at=run.finished_at,
        )
        for run in runs
    ]


@router.get("/notifications", response_model=list[NotificationOut])
def list_notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[NotificationOut]:
    rows = db.scalars(
        select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(30)
    ).all()
    return [
        NotificationOut(
            id=row.id,
            subject=row.subject,
            body=row.body,
            status=row.status,
            created_at=row.created_at,
            opened_at=row.opened_at,
        )
        for row in rows
    ]


@router.get("/notifications/{notification_id}/open.gif")
def open_notification(notification_id: str, db: Session = Depends(get_db)) -> Response:
    note = db.get(Notification, notification_id)
    if note is not None and note.opened_at is None:
        note.opened_at = utcnow()
        db.commit()
    return Response(content=PIXEL, media_type="image/gif")
