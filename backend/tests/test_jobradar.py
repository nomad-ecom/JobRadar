import os

os.environ["JOBRADAR_DATABASE_URL"] = "sqlite+pysqlite:////tmp/jobradar-test.db"
os.environ["JOBRADAR_SCHEDULER"] = "false"
os.environ["JOBRADAR_SAMPLE_SOURCE"] = "true"
os.environ["JOBRADAR_SECRET"] = "test-secret"
os.environ["JOBRADAR_ENV"] = "development"
os.environ["JOBRADAR_RESEND_API_KEY"] = ""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.crawlers.linkedin import parse_linkedin_html
from app.crawlers.sample import SAMPLE_JOBS
from app.crawlers.topcv import parse_topcv_html
from app.crawlers.vietnamworks import parse_vietnamworks_html
from app.db import reset_engine
from app.main import app
from app.models import Profile
from app.services.cv_parser import parse_cv_text
from app.services.matching import score_job
from app.services.salary import parse_salary
from app.textutil import dedup_hash


@pytest.fixture()
def client(monkeypatch):
    db_path = Path("/tmp/jobradar-test.db")
    if db_path.exists():
        db_path.unlink()
    reset_engine()

    def blocked(url: str):
        return 403, "Attention Required! Cloudflare", "text/html"

    monkeypatch.setattr("app.services.pipeline.http_fetch", blocked)
    with TestClient(app) as test_client:
        yield test_client
    reset_engine()
    if db_path.exists():
        db_path.unlink()


def test_dedup_ignores_accents_and_case():
    left = dedup_hash("Backend Engineer", "Công ty A", "Hà Nội")
    right = dedup_hash("backend  engineer", "Cong ty A", "Ha Noi")
    assert left == right


def test_salary_parser_reads_trieu_range():
    low, high, currency = parse_salary("30-45 triệu")
    assert (low, high, currency) == (30_000_000, 45_000_000, "VND")
    assert parse_salary("Thương lượng") == (None, None, "VND")


def test_cv_parser_reads_vietnamese_sections():
    parsed = parse_cv_text(
        "\n".join(
            [
                "Nguyen Van A",
                "Vi tri mong muon: Backend Engineer",
                "Ky nang: Python, FastAPI, PostgreSQL, Docker",
                "Kinh nghiem: 4 nam",
                "Dia diem: Ha Noi",
                "Muc luong: 30-45 trieu",
            ]
        )
    )
    assert parsed["desired_title"] == "Backend Engineer"
    assert "Python" in parsed["skills"]
    assert "FastAPI" in parsed["skills"]
    assert parsed["experience_years"] == 4
    assert "Hà Nội" in parsed["locations"]
    assert parsed["salary_min"] == 30_000_000
    assert parsed["salary_max"] == 45_000_000


def test_vietnamworks_parser_reads_embedded_jobs():
    html = """
    <script id="__NEXT_DATA__" type="application/json">{"props":{"pageProps":{"outstandingJobs":[
      {"jobTitle":"Backend Engineer","company":"Song Hong","location":"Hà Nội","prettySalary":"30-45 triệu",
       "url":"https://www.vietnamworks.com/backend-engineer-123456789-jd","isAnonymous":0,"skills":["Python"]}
    ]}}}</script>
    """
    jobs = parse_vietnamworks_html(html)
    assert len(jobs) == 1
    assert jobs[0].external_id == "123456789"
    assert jobs[0].salary_min == 30_000_000
    assert jobs[0].skills == ["Python"]


def test_topcv_and_linkedin_parsers():
    topcv = """
    <div class="job-item-search-result">
      <h3><a href="https://www.topcv.vn/viec-lam/backend-12345.html">Backend</a></h3>
      <a class="company">Cong ty A</a>
      <span class="city-text">Ha Noi</span>
      <span class="label-salary">20 triệu</span>
    </div>
    """
    linkedin = """
    <div class="base-search-card">
      <a class="base-card__full-link" href="https://www.linkedin.com/jobs/view/123456789"></a>
      <h3 class="base-search-card__title">Backend</h3>
      <h4 class="base-search-card__subtitle">Cong ty A</h4>
      <span class="job-search-card__location">Hanoi</span>
    </div>
    """
    assert parse_topcv_html(topcv)[0].company == "Cong ty A"
    assert parse_linkedin_html(linkedin)[0].external_id == "123456789"


def test_matching_ranks_a_backend_profile():
    profile = Profile(
        user_id="u",
        desired_title="Backend Engineer",
        skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
        experience_years=4,
        locations=["Hà Nội"],
        salary_min=30_000_000,
        salary_max=45_000_000,
        salary_currency="VND",
    )
    from app.models import Job

    scored = []
    for draft in SAMPLE_JOBS:
        job = Job(
            source=draft.source,
            title=draft.title,
            company=draft.company,
            location=draft.location,
            description=draft.description,
            salary_min=draft.salary_min,
            salary_max=draft.salary_max,
            salary_currency=draft.salary_currency,
            skills=draft.skills,
            url=draft.url,
        )
        scored.append((draft.external_id, score_job(profile, job)["score"]))
    by_id = dict(scored)
    assert by_id["sample-backend-python"] >= 70
    assert by_id["sample-fastapi"] >= 70
    assert sum(1 for _job_id, score in scored if score >= 70) >= 3
    assert by_id["sample-marketing"] < 40


def test_user_flow_matches_and_notifies(client):
    registered = client.post(
        "/auth/register",
        json={"email": "lan@example.com", "name": "Lan", "password": "matkhau123"},
    )
    assert registered.status_code == 200, registered.text
    token = registered.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    saved = client.put(
        "/profile",
        headers=headers,
        json={
            "desired_title": "Backend Engineer",
            "summary": "Lam API",
            "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
            "experience_years": 4,
            "locations": ["Hà Nội"],
            "salary_min": 30000000,
            "salary_max": 45000000,
            "salary_currency": "VND",
        },
    )
    assert saved.status_code == 200

    crawled = client.post("/crawl", headers=headers)
    assert crawled.status_code == 200, crawled.text
    by_source = {item["source"]: item for item in crawled.json()}
    assert by_source["sample"]["status"] == "ok"
    assert by_source["sample"]["jobs_new"] == 8
    assert by_source["topcv"]["status"] == "blocked"
    assert by_source["linkedin"]["status"] == "blocked"

    matches = client.get("/matches", headers=headers)
    assert matches.status_code == 200
    body = matches.json()
    high = [item for item in body if item["score"] >= 70]
    assert len(high) >= 3
    assert body[0]["score"] >= body[-1]["score"]

    stats = client.get("/matches/stats", headers=headers).json()
    assert stats["high"] >= 3
    assert stats["notified"] >= 3

    notes = client.get("/notifications", headers=headers)
    assert notes.status_code == 200
    assert notes.json()[0]["status"] == "logged"
    note_id = notes.json()[0]["id"]
    opened = client.get(f"/notifications/{note_id}/open.gif")
    assert opened.status_code == 200
    assert opened.headers["content-type"].startswith("image/gif")
    assert client.get("/matches/stats", headers=headers).json()["opened_notifications"] == 1

    match_id = high[0]["id"]
    updated = client.patch(f"/matches/{match_id}", headers=headers, json={"status": "saved"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "saved"
    detail = client.get(f"/matches/{match_id}", headers=headers)
    assert detail.status_code == 200
    applied = client.patch(f"/matches/{match_id}", headers=headers, json={"status": "applied"})
    assert applied.json()["status"] == "applied"

    prefs = client.put(
        "/preferences",
        headers=headers,
        json={"min_score": 80, "frequency": "daily", "sources": ["sample"], "email_enabled": True},
    )
    assert prefs.status_code == 200
    assert prefs.json()["min_score"] == 80

    rejected = client.post("/profile/cv", headers=headers, files={"file": ("notes.txt", b"hello", "text/plain")})
    assert rejected.status_code == 400
