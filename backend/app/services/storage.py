import re

import httpx

from app.config import Settings


def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", name or "cv.pdf")
    return cleaned[:80] or "cv.pdf"


def save_cv(settings: Settings, user_id: str, filename: str, data: bytes) -> str:
    stored_name = safe_filename(filename)
    if settings.supabase_storage_configured:
        path = f"{user_id}/{stored_name}"
        endpoint = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{settings.supabase_bucket}/{path}"
        response = httpx.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {settings.supabase_service_role_key}",
                "Content-Type": "application/pdf",
                "x-upsert": "true",
            },
            content=data,
            timeout=30,
        )
        response.raise_for_status()
        return f"supabase://{settings.supabase_bucket}/{path}"

    destination = settings.storage_path / user_id / stored_name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return str(destination)
