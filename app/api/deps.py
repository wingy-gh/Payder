from urllib.parse import urlsplit

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import read_session_token
from app.database.crud import users as users_crud
from app.database.db_core import get_db
from app.database.models import User

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def get_current_user(payder_session: str | None = Cookie(default=None), db: Session = Depends(get_db)) -> User:
    parsed = read_session_token(payder_session) if payder_session else None
    user = users_crud.get_by_id(db, parsed[0]) if parsed is not None else None
    # Версия токена в токене должна совпадать с версией у пользователя:
    # после выхода (logout) старые токены перестают работать.
    if user is None or parsed is None or user.token_version != parsed[1]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Войдите в аккаунт")
    return user


def require_same_origin(request: Request) -> None:
    """Защита от CSRF: запросы, меняющие данные, принимаются только со своего Origin."""
    if request.method in _SAFE_METHODS:
        return
    origin = request.headers.get("origin")
    if origin is None:
        return  # не браузер (curl, тесты, сервер-сервер)
    origin_host = urlsplit(origin).netloc
    allowed = {urlsplit(item).netloc for item in get_settings().allowed_origins}
    host = request.headers.get("host")
    if host:
        allowed.add(host)
    if not origin_host or origin_host not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Запрос с чужого источника")
