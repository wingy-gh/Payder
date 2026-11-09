from datetime import datetime, timezone

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.database.models import Activity, Card, CardView, Consent, Help, User

DELETED_USER_TITLE = "Вы помогли удалённому пользователю"


def export_user_data(db: Session, user: User) -> dict:
    """Все данные, которые сервис хранит о самом пользователе.

    Данные других людей (имена помощников и т.п.) не включаются.
    """
    cards = db.scalars(select(Card).where(Card.author_id == user.id).order_by(Card.id)).all()
    helps_given = db.execute(
        select(Help, Card.public_id)
        .join(Card, Help.card_id == Card.id)
        .where(Help.helper_id == user.id)
        .order_by(Help.id)
    ).all()
    helps_received = db.scalar(
        select(func.count()).select_from(Help).join(Card, Help.card_id == Card.id).where(Card.author_id == user.id)
    ) or 0
    views_made = db.execute(
        select(CardView.created_at, Card.public_id)
        .join(Card, CardView.card_id == Card.id)
        .where(CardView.viewer_id == user.id)
        .order_by(CardView.id)
    ).all()
    activities = db.scalars(select(Activity).where(Activity.user_id == user.id).order_by(Activity.id)).all()
    consents = db.scalars(select(Consent).where(Consent.user_id == user.id).order_by(Consent.id)).all()

    return {
        "exported_at": datetime.now(timezone.utc),
        "profile": {
            "name": user.name,
            "username": user.username,
            "phone": user.phone,
            "bank": user.bank,
            "requisites": user.requisites,
            "created_at": user.created_at,
        },
        "cards": [
            {
                "id": card.public_id,
                "amount": card.amount,
                "purpose": card.purpose,
                "category": card.category,
                "is_active": card.is_active,
                "created_at": card.created_at,
            }
            for card in cards
        ],
        "helps_given": [
            {"card": public_id, "amount": help_row.amount, "created_at": help_row.created_at}
            for help_row, public_id in helps_given
        ],
        "consents": [
            {"document": item.document, "version": item.version, "accepted_at": item.accepted_at}
            for item in consents
        ],
        "helps_received_count": int(helps_received),
        "views_made": [{"card": public_id, "created_at": created_at} for created_at, public_id in views_made],
        "activities": [
            {
                "title": item.title,
                "amount_label": item.amount_label,
                "happened_at": item.happened_at,
                "kind": item.kind,
                "created_at": item.created_at,
            }
            for item in activities
        ],
    }


def delete_user(db: Session, user: User) -> None:
    """Полностью удаляет пользователя и его данные.

    Карточки, помощи, просмотры и история удаляются каскадом на уровне БД
    (ondelete=CASCADE; для SQLite включён PRAGMA foreign_keys). Имя удаляемого
    человека остаётся текстом в чужой истории («Вы помогли Имя»), его обезличиваем.
    """
    db.execute(
        update(Activity)
        .where(Activity.title == f"Вы помогли {user.name}")
        .values(title=DELETED_USER_TITLE)
        .execution_options(synchronize_session=False)
    )
    db.execute(delete(User).where(User.id == user.id).execution_options(synchronize_session=False))
    db.commit()
