import re

from pypdf import PdfReader

from app.services.salary import parse_salary
from app.textutil import fold, unique_keep

SKILL_LEXICON = [
    "Python", "Java", "JavaScript", "TypeScript", "Go", "Golang", "PHP", "C#", "C++", "Ruby", "Kotlin", "Swift",
    "FastAPI", "Django", "Flask", "Spring", "Node.js", "React", "Vue", "Angular", "Next.js", "Laravel",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQL", "Docker", "Kubernetes", "AWS", "GCP", "Azure",
    "Git", "Linux", "REST", "GraphQL", "Airflow", "Spark", "Pandas", "Excel", "Power BI", "Tableau",
    "Figma", "SEO", "Google Ads", "Facebook Ads", "Tiếng Anh", "English", "Scrum", "Jira",
]


def extract_pdf_text(data: bytes) -> str:
    reader = PdfReader(__import__("io").BytesIO(data))
    pages = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(pages).strip()


def _section(text: str, headers: tuple[str, ...], stop: tuple[str, ...]) -> str:
    folded_lines = [(fold(line), line) for line in text.splitlines()]
    start = None
    chunk: list[str] = []
    for index, (folded, original) in enumerate(folded_lines):
        if any(folded.startswith(header) or folded == header for header in headers):
            if ":" in original:
                chunk.append(original.split(":", 1)[1])
            start = index + 1
            break
    if start is None:
        return ""
    for folded, original in folded_lines[start:]:
        if any(folded.startswith(header) for header in stop):
            break
        chunk.append(original)
    return "\n".join(chunk)


def _skills_from_section(section: str) -> list[str]:
    pieces = re.split(r"[\n,;•|/]+", section)
    return [piece.strip(" -:\t") for piece in pieces if 1 < len(piece.strip()) <= 40]


def _lexicon_hits(text: str) -> list[str]:
    folded = fold(text)
    found: list[str] = []
    for skill in SKILL_LEXICON:
        needle = fold(skill)
        if re.search(rf"(^|[^a-z0-9]){re.escape(needle)}([^a-z0-9]|$)", folded):
            found.append(skill)
    return found


def _experience_years(text: str) -> float | None:
    found = re.findall(r"(\d+(?:[.,]\d+)?)\s*\+?\s*(?:năm|nam|years|yrs)\b", fold(text))
    values = [float(item.replace(",", ".")) for item in found if float(item.replace(",", ".")) <= 40]
    if not values:
        return None
    return max(values)


def _line_after(text: str, labels: tuple[str, ...]) -> str:
    for line in text.splitlines():
        folded = fold(line)
        for label in labels:
            if folded.startswith(label):
                raw = line.split(":", 1)[-1] if ":" in line else line
                return raw.strip(" -:\t")
    return ""


def _locations(text: str) -> list[str]:
    known = ["Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Hải Phòng", "Cần Thơ", "Remote", "Toàn quốc"]
    folded = fold(text)
    hits = [name for name in known if fold(name) in folded]
    explicit = _line_after(text, ("dia diem", "địa điểm", "location", "noi lam viec", "nơi làm việc"))
    if explicit:
        hits.extend(part.strip() for part in re.split(r"[,/]| và ", explicit))
    return unique_keep(hits)


def parse_cv_text(text: str) -> dict:
    cleaned = text.replace("\x00", "").strip()
    stop = (
        "kinh nghiem", "hoc van", "hoc vấn", "chung chi", "chứng chỉ", "muc tieu", "mục tiêu",
        "du an", "dự án", "giai thuong", "hoat dong", "tham chieu",
    )
    skill_section = _section(
        cleaned,
        ("ky nang", "kỹ năng", "skills", "technical skills"),
        stop + ("kinh nghiem lam viec", "kinh nghiệm"),
    )
    skills = unique_keep(_skills_from_section(skill_section) + _lexicon_hits(cleaned))
    title = _line_after(cleaned, ("vi tri mong muon", "vị trí mong muốn", "vi tri", "vị trí", "desired position", "objective"))
    if not title:
        for line in cleaned.splitlines():
            if 3 <= len(line.strip()) <= 80:
                title = line.strip()
                break
    salary_line = _line_after(cleaned, ("muc luong", "mức lương", "luong", "lương mong muon", "salary", "expected salary"))
    salary_min, salary_max, currency = parse_salary(salary_line or cleaned)
    if not salary_line:
        salary_min, salary_max = None, None
    locations = _locations(cleaned)
    years = _experience_years(cleaned)
    summary_line = _line_after(cleaned, ("tom tat", "tóm tắt", "summary", "gioi thieu", "giới thiệu"))
    return {
        "desired_title": title[:200],
        "summary": (summary_line or cleaned[:400])[:1000],
        "skills": skills[:40],
        "experience_years": years,
        "locations": locations[:8],
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_currency": currency,
        "cv_text": cleaned[:20000],
    }
