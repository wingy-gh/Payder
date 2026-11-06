import random
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.database.models import Card, CardView, Help, User
from app.menu.items import CATEGORY_COLORS


def list_active(db: Session, *, exclude_author_id: int | None = None) -> list[Card]:
    stmt = (
        select(Card)
        .options(joinedload(Card.author))
        .where(Card.is_active.is_(True))
        .order_by(Card.created_at.desc())
    )
    if exclude_author_id is not None:
        stmt = stmt.where(Card.author_id != exclude_author_id)
    return list(db.scalars(stmt).unique().all())


def list_all(db: Session) -> list[Card]:
    stmt = select(Card).options(joinedload(Card.author)).order_by(Card.created_at.desc())
    return list(db.scalars(stmt).unique().all())


def get_by_public_id(db: Session, public_id: str) -> Card | None:
    return db.scalar(
        select(Card).options(joinedload(Card.author)).where(Card.public_id == public_id)
    )


def generate_public_id(db: Session) -> str:
    for _ in range(40):
        candidate = f"PD-{random.randint(10000, 99999)}"
        exists = db.scalar(select(Card.id).where(Card.public_id == candidate))
        if exists is None:
            return candidate
    raise RuntimeError("Не удалось сгенерировать идентификатор карточки")


def create_card(
    db: Session,
    *,
    author: User,
    amount: int,
    purpose: str,
    category: str,
) -> Card:
    card = Card(
        public_id=generate_public_id(db),
        amount=amount,
        purpose=purpose.strip(),
        category=category,
        color=CATEGORY_COLORS.get(category, "#D9F99D"),
        author_id=author.id,
        is_active=True,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    db.refresh(card, attribute_names=["author"])
    return card


def deactivate(db: Session, card: Card) -> None:
    card.is_active = False
    db.add(card)
    db.commit()


def count_active_for_author(db: Session, author_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(Card).where(
            Card.author_id == author_id,
            Card.is_active.is_(True),
        )
    ) or 0


def register_view(db: Session, card: Card, viewer_id: int | None) -> None:
    db.add(CardView(card_id=card.id, viewer_id=viewer_id))
    db.commit()


def collected_for_author(
    db: Session,
    author_id: int,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
) -> int:
    stmt = (
        select(func.coalesce(func.sum(Help.amount), 0))
        .join(Card, Help.card_id == Card.id)
        .where(Card.author_id == author_id)
    )
    if since is not None:
        stmt = stmt.where(Help.created_at >= since)
    if until is not None:
        stmt = stmt.where(Help.created_at < until)
    value = db.scalar(stmt)
    return int(value or 0)
