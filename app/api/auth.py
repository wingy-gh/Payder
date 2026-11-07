from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.security import create_session_token, hash_password, verify_password
from app.database.crud import users as users_crud
from app.database.db_core import get_db
from app.schemas.auth import LoginIn, RegisterIn

router = APIRouter(prefix="/auth", tags=["authentication"])
COOKIE_NAME = "payder_session"


def _set_session(response: Response, user_id: int, request: Request) -> None:
    response.set_cookie(COOKIE_NAME, create_session_token(user_id), httponly=True,
                        secure=request.url.scheme == "https", samesite="lax", max_age=60 * 60 * 24 * 14, path="/")


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    username = payload.username.strip().lower()
    if users_crud.get_by_username(db, username):
        raise HTTPException(status_code=409, detail="Это имя пользователя уже занято")
    user = users_crud.create_user(db, name=payload.name, username=username,
                                  password_hash=hash_password(payload.password))
    _set_session(response, user.id, request)
    return {"id": user.id, "name": user.name, "username": user.username}


@router.post("/login")
def login(payload: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    user = users_crud.get_by_username(db, payload.username.strip().lower())
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    _set_session(response, user.id, request)
    return {"id": user.id, "name": user.name, "username": user.username}


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}
