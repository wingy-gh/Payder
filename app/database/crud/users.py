from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import User


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def update_profile(
    db: Session,
    user: User,
    *,
    name: str,
    phone: str,
    bank: str,
    requisites: str,
) -> User:
    user.name = name.strip()
    user.phone = phone.strip()
    user.bank = bank.strip()
    user.requisites = requisites.strip()
    user.initials = _initials(user.name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _initials(name: str) -> str:
    parts = [p for p in name.replace(".", " ").split() if p]
    if not parts:
        return "??"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()
