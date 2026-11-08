from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.ratelimit import RateLimiter
from app.database.crud import cards as cards_crud
from app.database.crud import helps as helps_crud
from app.database.db_core import get_db
from app.database.models import User
from app.menu.items import CATEGORIES
from app.schemas.card import CardCreate, CardPublic, HelpOut

router = APIRouter(prefix="/cards", tags=["cards"])

# Промахи по несуществующим id: перебор идентификаторов карточек блокируется.
_probe_limiter = RateLimiter(limit=30, window=10 * 60)


def _get_active_card(db: Session, public_id: str, user: User):
    key = f"user:{user.id}"
    _probe_limiter.check(key)
    card = cards_crud.get_by_public_id(db, public_id)
    if card is None or not card.is_active:
        _probe_limiter.hit(key)
        raise HTTPException(status_code=404, detail="Карточка не найдена")
    return card


def _public(card) -> CardPublic:
    return CardPublic(
        id=card.public_id,
        amount=card.amount,
        purpose=card.purpose,
        category=card.category,
        author=card.author.name,
        initials=card.author.initials,
        color=card.color,
    )


@router.get("", response_model=list[CardPublic])
def list_cards(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[CardPublic]:
    cards = cards_crud.list_active(db, exclude_author_id=user.id)
    return [_public(card) for card in cards]


@router.post("", response_model=CardPublic, status_code=status.HTTP_201_CREATED)
def create_card(
    payload: CardCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CardPublic:
    if payload.category not in CATEGORIES:
        raise HTTPException(status_code=422, detail="Неизвестная категория")
    if cards_crud.count_active_for_author(db, user.id) >= 3:
        raise HTTPException(status_code=400, detail="Можно держать не больше 3 активных карточек")
    card = cards_crud.create_card(
        db,
        author=user,
        amount=payload.amount,
        purpose=payload.purpose,
        category=payload.category,
    )
    return _public(card)


@router.post("/{public_id}/view", status_code=status.HTTP_204_NO_CONTENT)
def view_card(
    public_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    card = _get_active_card(db, public_id, user)
    cards_crud.register_view(db, card, user.id)


@router.post("/{public_id}/help", response_model=HelpOut)
def help_card(
    public_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> HelpOut:
    card = _get_active_card(db, public_id, user)
    if card.author_id == user.id:
        raise HTTPException(status_code=400, detail="Нельзя помочь своей карточке")
    # Повторный показ уже открытых реквизитов лимит не расходует, новые карточки считаются за сутки.
    if not helps_crud.has_helped(db, card_id=card.id, helper_id=user.id):
        since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
        if helps_crud.count_since(db, user.id, since) >= get_settings().help_daily_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Достигнут суточный лимит открытия реквизитов. Попробуйте завтра",
            )
    helps_crud.record_help(db, card=card, helper=user)
    return HelpOut(
        id=card.public_id,
        author=card.author.name,
        bank=card.author.bank,
        requisites=card.author.requisites,
    )
