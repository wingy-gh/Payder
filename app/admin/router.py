from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.ratelimit import RateLimiter
from app.core.security import ADMIN_TTL, create_admin_token, read_admin_token, verify_admin_password
from app.database.crud import cards as cards_crud
from app.database.db_core import get_db
from app.database.models import Help, User
from app.schemas.auth import AdminLoginIn

router = APIRouter(tags=["admin"])

_admin_login_by_ip = RateLimiter(limit=5, window=15 * 60)


def require_admin(x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")) -> None:
    if not x_admin_token or not read_admin_token(x_admin_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Нет доступа")


@router.post("/login")
def login(payload: AdminLoginIn, request: Request) -> dict:
    ip = request.client.host if request.client else "unknown"
    _admin_login_by_ip.check(ip)
    if not verify_admin_password(payload.password):
        _admin_login_by_ip.hit(ip)
        raise HTTPException(status_code=401, detail="Неверный пароль")
    _admin_login_by_ip.reset(ip)
    # Возвращаем подписанный токен с ограниченным сроком, а не сам пароль.
    return {"token": create_admin_token(), "expires_in": ADMIN_TTL}


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
