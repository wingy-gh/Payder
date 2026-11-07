from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import User


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def create_user(db: Session, *, name: str, username: str, password_hash: str) -> User:
    parts = [part for part in name.strip().split() if part]
    initials = (parts[0][0] + (parts[1][0] if len(parts) > 1 else parts[0][1:2])).upper()
    user = User(name=name.strip(), username=username.strip().lower(), password_hash=password_hash,
                phone="", bank="", requisites="", initials=initials)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_profile(db: Session, user: User, *, name: str, phone: str, bank: str, requisites: str) -> User:
    user.name, user.phone, user.bank, user.requisites = name.strip(), phone.strip(), bank.strip(), requisites.strip()
    parts = [p for p in user.name.replace(".", " ").split() if p]
    user.initials = (parts[0][0] + (parts[1][0] if len(parts) > 1 else parts[0][1:2])).upper()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
