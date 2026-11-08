from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.ratelimit import RateLimiter
from app.core.security import SESSION_TTL, create_session_token, dummy_verify, hash_password, read_session_token, verify_password
from app.database.crud import users as users_crud
from app.database.db_core import get_db
from app.database.models import User
from app.schemas.auth import LoginIn, RegisterIn

router = APIRouter(prefix="/auth", tags=["authentication"])
COOKIE_NAME = "payder_session"

# Ограничения на перебор паролей и массовую регистрацию (в памяти процесса).
_login_by_ip = RateLimiter(limit=30, window=15 * 60)
_login_by_pair = RateLimiter(limit=5, window=15 * 60)
_register_by_ip = RateLimiter(limit=10, window=60 * 60)


def _client_ip(request: Request) -> str:
    # X-Forwarded-For не используем: его легко подделать. За прокси запускайте
    # uvicorn с --proxy-headers и --forwarded-allow-ips, тогда request.client станет настоящим.
    return request.client.host if request.client else "unknown"


def _set_session(response: Response, user: User, request: Request) -> None:
    response.set_cookie(
        COOKIE_NAME,
        create_session_token(user.id, user.token_version),
        httponly=True,
        secure=get_settings().cookie_secure or request.url.scheme == "https",
        samesite="lax",
        max_age=SESSION_TTL,
        path="/",
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    ip = _client_ip(request)
    _register_by_ip.check(ip)
    _register_by_ip.hit(ip)
    username = payload.username.strip().lower()
    if users_crud.get_by_username(db, username):
        raise HTTPException(status_code=409, detail="Это имя пользователя уже занято")
    user = users_crud.create_user(db, name=payload.name, username=username,
                                  password_hash=hash_password(payload.password))
    _set_session(response, user, request)
    return {"id": user.id, "name": user.name, "username": user.username}


@router.post("/login")
def login(payload: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    ip = _client_ip(request)
    username = payload.username.strip().lower()
    pair = f"{ip}|{username}"
    _login_by_ip.check(ip)
    _login_by_pair.check(pair)

    user = users_crud.get_by_username(db, username)
    if user is None:
        dummy_verify(payload.password)  # выравниваем время ответа
        valid = False
    else:
        valid = verify_password(payload.password, user.password_hash)

    if user is None or not valid:
        _login_by_ip.hit(ip)
        _login_by_pair.hit(pair)
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    _login_by_pair.reset(pair)
    _set_session(response, user, request)
    return {"id": user.id, "name": user.name, "username": user.username}


@router.post("/logout")
def logout(
    response: Response,
    payder_session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> dict:
    # Увеличиваем версию токена: все ранее выданные токены этого пользователя
    # (в том числе украденные) перестают действовать. Это выход со всех устройств.
    parsed = read_session_token(payder_session) if payder_session else None
    if parsed is not None:
        user = users_crud.get_by_id(db, parsed[0])
        if user is not None and user.token_version == parsed[1]:
            users_crud.bump_token_version(db, user)
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}
