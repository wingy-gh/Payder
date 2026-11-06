from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.database.crud import cards as cards_crud
from app.database.db_core import get_db
from app.database.models import Help, User

router = APIRouter(tags=["admin"])


def require_admin(x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")) -> None:
    settings = get_settings()
    if not x_admin_token or x_admin_token != settings.admin_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Нет доступа")


@router.post("/login")
def login(payload: dict) -> dict:
    password = str(payload.get("password", ""))
    if password != get_settings().admin_password:
        raise HTTPException(status_code=401, detail="Неверный пароль")
    return {"token": get_settings().admin_password}


@router.get("/cards")
def admin_cards(_: None = Depends(require_admin), db: Session = Depends(get_db)) -> list[dict]:
    cards = cards_crud.list_all(db)
    return [
        {
            "id": card.id,
            "public_id": card.public_id,
            "amount": card.amount,
            "purpose": card.purpose,
            "category": card.category,
            "author": card.author.name,
            "is_active": card.is_active,
        }
        for card in cards
    ]


@router.post("/cards/{card_id}/toggle")
def toggle_card(card_id: int, _: None = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    from app.database.models import Card

    card = db.get(Card, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Карточка не найдена")
    card.is_active = not card.is_active
    db.add(card)
    db.commit()
    return {"id": card.id, "is_active": card.is_active}


@router.get("/users")
def admin_users(_: None = Depends(require_admin), db: Session = Depends(get_db)) -> list[dict]:
    users = db.scalars(select(User).order_by(User.id)).all()
    return [
        {
            "id": user.id,
            "name": user.name,
            "username": user.username,
            "bank": user.bank,
        }
        for user in users
    ]


@router.get("/helps")
def admin_helps(_: None = Depends(require_admin), db: Session = Depends(get_db)) -> list[dict]:
    helps = db.scalars(select(Help).options(joinedload(Help.card), joinedload(Help.helper)).order_by(Help.id.desc())).unique().all()
    return [
        {
            "id": item.id,
            "card": item.card.public_id,
            "helper": item.helper.name,
            "amount": item.amount,
        }
        for item in helps
    ]
