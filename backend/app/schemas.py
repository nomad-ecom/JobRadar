from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    name: str


class AuthOut(BaseModel):
    access_token: str
    user: UserOut


class ProfileIn(BaseModel):
    desired_title: str = ""
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    experience_years: float | None = None
    locations: list[str] = Field(default_factory=list)
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str = "VND"


class ProfileOut(ProfileIn):
    cv_path: str = ""
    updated_at: datetime | None = None


class PreferenceIn(BaseModel):
    min_score: int = Field(default=70, ge=0, le=100)
    frequency: str = "instant"
    sources: list[str] = Field(default_factory=list)
    email_enabled: bool = True


class PreferenceOut(PreferenceIn):
    last_digest_at: datetime | None = None


class JobOut(BaseModel):
    id: str
    source: str
    title: str
    company: str
    location: str
    salary_text: str
    salary_min: int | None
    salary_max: int | None
    salary_currency: str
    description: str
    url: str
    skills: list[str]
    crawled_at: datetime


class MatchOut(BaseModel):
    id: str
    score: int
    status: str
    breakdown: dict
    notified_at: datetime | None
    created_at: datetime
    job: JobOut


class MatchUpdate(BaseModel):
    status: str


class StatsOut(BaseModel):
    total: int
    high: int
    new: int
    saved: int
    applied: int
    notified: int
    opened_notifications: int


class CrawlRunOut(BaseModel):
    id: str
    source: str
    status: str
    jobs_found: int
    jobs_new: int
    message: str
    started_at: datetime
    finished_at: datetime


class NotificationOut(BaseModel):
    id: str
    subject: str
    body: str
    status: str
    created_at: datetime
    opened_at: datetime | None
