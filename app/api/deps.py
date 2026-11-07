from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import read_session_token
from app.database.crud import users as users_crud
from app.database.db_core import get_db
from app.database.models import User


def get_current_user(payder_session: str | None = Cookie(default=None), db: Session = Depends(get_db)) -> User:
    user_id = read_session_token(payder_session) if payder_session else None
    user = users_crud.get_by_id(db, user_id) if user_id is not None else None
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Войдите в аккаунт")
    return user
