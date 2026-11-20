from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class JobDraft:
    source: str
    external_id: str
    title: str
    company: str
    location: str
    url: str
    description: str = ""
    salary_text: str = ""
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str = "VND"
    skills: list[str] = field(default_factory=list)
    posted_at: datetime | None = None


@dataclass
class CrawlResult:
    source: str
    status: str
    message: str = ""
    jobs: list[JobDraft] = field(default_factory=list)
