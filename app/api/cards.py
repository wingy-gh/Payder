from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.crud import cards as cards_crud
from app.database.crud import helps as helps_crud
from app.database.db_core import get_db
from app.database.models import User
from app.menu.items import CATEGORIES
from app.schemas.card import CardCreate, CardPublic, HelpOut

router = APIRouter(prefix="/cards", tags=["cards"])


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
    card = cards_crud.get_by_public_id(db, public_id)
    if card is None or not card.is_active:
        raise HTTPException(status_code=404, detail="Карточка не найдена")
    cards_crud.register_view(db, card, user.id)


@router.post("/{public_id}/help", response_model=HelpOut)
def help_card(
    public_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> HelpOut:
    card = cards_crud.get_by_public_id(db, public_id)
    if card is None or not card.is_active:
        raise HTTPException(status_code=404, detail="Карточка не найдена")
    if card.author_id == user.id:
        raise HTTPException(status_code=400, detail="Нельзя помочь своей карточке")
    helps_crud.record_help(db, card=card, helper=user)
    return HelpOut(
        id=card.public_id,
        author=card.author.name,
        bank=card.author.bank,
        requisites=card.author.requisites,
    )
