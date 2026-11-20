import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException

PBKDF2_ITERATIONS = 210_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations))
    return secrets.compare_digest(digest.hex(), digest_hex)


def create_token(user_id: str, secret: str, days: int = 7) -> str:
    payload = {"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(days=days)}
    return jwt.encode(payload, secret, algorithm="HS256")


def read_token(token: str, secret: str) -> str:
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Phiên đăng nhập không hợp lệ") from exc
    subject = payload.get("sub")
    if not subject:
        raise HTTPException(status_code=401, detail="Phiên đăng nhập không hợp lệ")
    return str(subject)
