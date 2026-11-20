from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.models import User
from app.security import read_token

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Bạn cần đăng nhập")
    user_id = read_token(credentials.credentials, settings.secret)
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Phiên đăng nhập không hợp lệ")
    return user
