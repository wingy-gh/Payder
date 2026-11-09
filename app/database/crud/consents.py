from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.legal import LEGAL_DOCS, LEGAL_VERSION
from app.database.models import Consent, User


def has_current(db: Session, user_id: int) -> bool:
    """Принял ли пользователь все документы текущей версии."""
    accepted = set(
        db.scalars(
            select(Consent.document).where(Consent.user_id == user_id, Consent.version == LEGAL_VERSION)
        ).all()
    )
    return all(doc in accepted for doc in LEGAL_DOCS)


def record_current(db: Session, user: User) -> None:
    """Фиксирует принятие текущей версии документов (версия, дата и время ставятся сервером)."""
    accepted = set(
        db.scalars(
            select(Consent.document).where(Consent.user_id == user.id, Consent.version == LEGAL_VERSION)
        ).all()
    )
    for doc in LEGAL_DOCS:
        if doc not in accepted:
            db.add(Consent(user_id=user.id, document=doc, version=LEGAL_VERSION))
    db.commit()
