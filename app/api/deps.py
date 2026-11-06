from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.crud import users as users_crud
from app.database.db_core import get_db
from app.database.models import User


def get_current_user(db: Session = Depends(get_db)) -> User:
    settings = get_settings()
    user = users_crud.get_by_username(db, settings.current_username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")
    return user
