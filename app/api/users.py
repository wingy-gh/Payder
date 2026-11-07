from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.auth import COOKIE_NAME
from app.api.deps import get_current_user
from app.core.ratelimit import RateLimiter
from app.core.security import verify_password
from app.database.crud import cards as cards_crud
from app.database.crud import helps as helps_crud
from app.database.crud import privacy as privacy_crud
from app.database.crud import users as users_crud
from app.database.db_core import get_db
from app.database.models import User
from app.menu.items import BANKS
from app.schemas.user import DeleteAccountIn, ProfileOut, ProfileUpdate

router = APIRouter(prefix="/profile", tags=["profile"])

# Защита подтверждения паролем от перебора (на случай украденной сессии).
_delete_limiter = RateLimiter(limit=5, window=15 * 60)


def _profile_out(db: Session, user: User) -> ProfileOut:
    return ProfileOut(
        name=user.name,
        username=user.username,
        phone=user.phone,
        bank=user.bank,
        requisites=user.requisites,
        initials=user.initials,
        helped=helps_crud.helped_people_count(db, user.id),
        cards=cards_crud.count_active_for_author(db, user.id),
    )


@router.get("", response_model=ProfileOut)
def get_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> ProfileOut:
    return _profile_out(db, user)


@router.put("", response_model=ProfileOut)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProfileOut:
    if payload.bank not in BANKS:
        raise HTTPException(status_code=422, detail="Неизвестный банк")
    user = users_crud.update_profile(
        db,
        user,
        name=payload.name,
        phone=payload.phone,
        bank=payload.bank,
        requisites=payload.requisites,
    )
    return _profile_out(db, user)


@router.get("/export")
def export_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> JSONResponse:
    """Выгрузка всех данных о пользователе одним JSON-файлом."""
    data = privacy_crud.export_user_data(db, user)
    return JSONResponse(
        content=jsonable_encoder(data),
        headers={
            "Content-Disposition": 'attachment; filename="payder-data.json"',
            "Cache-Control": "no-store",
        },
    )


@router.delete("")
def delete_account(
    payload: DeleteAccountIn,
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Безвозвратное удаление аккаунта и всех его данных. Нужен пароль."""
    key = f"user:{user.id}"
    _delete_limiter.check(key)
    if not verify_password(payload.password, user.password_hash):
        _delete_limiter.hit(key)
        raise HTTPException(status_code=401, detail="Неверный пароль")
    privacy_crud.delete_user(db, user)
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}
