import re

from app.models import Job, Profile
from app.textutil import fold, tokens

REMOTE_MARKERS = ("remote", "toan quoc", "linh hoat", "hybrid", "work from home")


def _years_required(job: Job) -> float | None:
    blob = fold(f"{job.title} {job.description}")
    found = re.findall(r"(\d+(?:[.,]\d+)?)\s*\+?\s*(?:nam|years|yrs)\b", blob)
    values = [float(item.replace(",", ".")) for item in found if float(item.replace(",", ".")) <= 20]
    if not values:
        return None
    return min(values)


def _skill_hits(profile: Profile, job: Job) -> list[str]:
    haystack = fold(" ".join([job.title, job.description, job.company, " ".join(job.skills or [])]))
    hits: list[str] = []
    for skill in profile.skills or []:
        needle = fold(skill)
        if len(needle) < 2:
            continue
        if re.search(rf"(^|[^a-z0-9+#]){re.escape(needle)}([^a-z0-9+#]|$)", haystack):
            hits.append(skill)
    return hits


def _ranges_overlap(a_min: int | None, a_max: int | None, b_min: int | None, b_max: int | None) -> str:
    if a_min is None and a_max is None or b_min is None and b_max is None:
        return "unknown"
    left = 0 if a_min is None else a_min
    right = 10**15 if a_max is None else a_max
    other_left = 0 if b_min is None else b_min
    other_right = 10**15 if b_max is None else b_max
    if right < other_left or other_right < left:
        return "apart"
    return "overlap"


def score_job(profile: Profile, job: Job) -> dict:
    reasons: list[str] = []

    hits = _skill_hits(profile, job)
    skill_total = len(profile.skills or [])
    if skill_total == 0:
        skill_points = 16
        reasons.append("Hồ sơ chưa có kỹ năng để so")
    else:
        ratio = len(hits) / skill_total
        skill_points = round(40 * ratio)
        if hits:
            reasons.append("Trùng kỹ năng: " + ", ".join(hits[:6]))
        else:
            reasons.append("Không thấy kỹ năng trong hồ sơ xuất hiện ở tin này")

    required = _years_required(job)
    years = profile.experience_years
    if required is None or years is None:
        experience_points = 12
        reasons.append("Chưa đủ dữ liệu số năm kinh nghiệm")
    elif years + 0.25 >= required:
        experience_points = 20
        reasons.append(f"Kinh nghiệm {years:g} năm đáp ứng mức khoảng {required:g} năm")
    elif years + 1 >= required:
        experience_points = 10
        reasons.append(f"Kinh nghiệm thấp hơn khoảng {required:g} năm một chút")
    else:
        experience_points = 3
        reasons.append(f"Tin cần khoảng {required:g} năm, hồ sơ đang {years:g} năm")

    title_tokens = tokens(profile.desired_title)
    job_title_tokens = set(tokens(job.title))
    if not title_tokens:
        title_points = 6
    else:
        overlap = [token for token in title_tokens if token in job_title_tokens]
        title_points = round(15 * len(overlap) / len(title_tokens))
        if overlap:
            reasons.append("Vị trí gần với tiêu đề tin")
        else:
            reasons.append("Tiêu đề tin khác vị trí mong muốn")

    job_location = fold(job.location)
    profile_locations = [fold(item) for item in (profile.locations or [])]
    if not profile_locations:
        location_points = 8
        reasons.append("Hồ sơ chưa chọn địa điểm")
    elif any(marker in job_location for marker in REMOTE_MARKERS):
        location_points = 15
        reasons.append("Tin remote hoặc không giới hạn địa điểm")
    elif any(item and (item in job_location or job_location in item) for item in profile_locations):
        location_points = 15
        reasons.append(f"Đúng địa điểm: {job.location}")
    else:
        location_points = 0
        reasons.append(f"Khác địa điểm: {job.location or 'không rõ'}")

    if (profile.salary_currency or "VND") != (job.salary_currency or "VND") and job.salary_min:
        salary_points = 5
        reasons.append("Khác đơn vị lương, chưa so được")
        salary_relation = "currency"
    else:
        salary_relation = _ranges_overlap(profile.salary_min, profile.salary_max, job.salary_min, job.salary_max)
        if salary_relation == "unknown":
            salary_points = 5
            reasons.append("Một trong hai bên chưa có mức lương")
        elif salary_relation == "overlap":
            salary_points = 10
            reasons.append("Mức lương giao với khoảng mong muốn")
        else:
            salary_points = 1
            reasons.append("Mức lương lệch khỏi khoảng mong muốn")

    score = max(0, min(100, skill_points + experience_points + title_points + location_points + salary_points))
    return {
        "score": score,
        "skills": skill_points,
        "experience": experience_points,
        "title": title_points,
        "location": location_points,
        "salary": salary_points,
        "matched_skills": hits,
        "reasons": reasons,
    }
