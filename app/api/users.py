from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.crud import cards as cards_crud
from app.database.crud import helps as helps_crud
from app.database.crud import users as users_crud
from app.database.db_core import get_db
from app.database.models import User
from app.menu.items import BANKS
from app.schemas.user import ProfileOut, ProfileUpdate

router = APIRouter(prefix="/profile", tags=["profile"])


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
