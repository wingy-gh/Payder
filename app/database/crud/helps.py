from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import Activity, Card, Help, User


def record_help(db: Session, *, card: Card, helper: User, amount: int = 0) -> Help:
    existing = db.scalar(
        select(Help).where(Help.card_id == card.id, Help.helper_id == helper.id)
    )
    if existing:
        return existing

    help_row = Help(card_id=card.id, helper_id=helper.id, amount=amount)
    db.add(help_row)
    db.add(
        Activity(
            user_id=card.author_id,
            title="Новый перевод",
            amount_label="реквизиты открыты",
            happened_at="Только что",
            kind="in",
        )
    )
    db.add(
        Activity(
            user_id=helper.id,
            title=f"Вы помогли {card.author.name}",
            amount_label="реквизиты открыты",
            happened_at="Только что",
            kind="out",
        )
    )
    db.commit()
    db.refresh(help_row)
    return help_row


def has_helped(db: Session, *, card_id: int, helper_id: int) -> bool:
    return db.scalar(
        select(Help.id).where(Help.card_id == card_id, Help.helper_id == helper_id)
    ) is not None


def count_since(db: Session, helper_id: int, since: datetime) -> int:
    """Сколько раз пользователь открыл реквизиты с момента `since`."""
    return db.scalar(
        select(func.count()).select_from(Help).where(Help.helper_id == helper_id, Help.created_at >= since)
    ) or 0


def helped_people_count(
    db: Session,
    helper_id: int,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
) -> int:
    stmt = select(func.count()).select_from(Help).where(Help.helper_id == helper_id)
    if since is not None:
        stmt = stmt.where(Help.created_at >= since)
    if until is not None:
        stmt = stmt.where(Help.created_at < until)
    return db.scalar(stmt) or 0


def helped_amount(
    db: Session,
    helper_id: int,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
) -> int:
    stmt = select(func.coalesce(func.sum(Help.amount), 0)).where(Help.helper_id == helper_id)
    if since is not None:
        stmt = stmt.where(Help.created_at >= since)
    if until is not None:
        stmt = stmt.where(Help.created_at < until)
    value = db.scalar(stmt)
    return int(value or 0)
