from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db_core import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    # Растёт при выходе: токены с прежней версией перестают действовать.
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    phone: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    bank: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    requisites: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    initials: Mapped[str] = mapped_column(String(8), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cards: Mapped[list["Card"]] = relationship(back_populates="author")
    helps_given: Mapped[list["Help"]] = relationship(
        back_populates="helper",
        foreign_keys="Help.helper_id",
    )


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    color: Mapped[str] = mapped_column(String(16), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    author: Mapped[User] = relationship(back_populates="cards")
    helps: Mapped[list["Help"]] = relationship(back_populates="card", cascade="all, delete-orphan")
    views: Mapped[list["CardView"]] = relationship(back_populates="card", cascade="all, delete-orphan")


class Help(Base):
    __tablename__ = "helps"
    __table_args__ = (UniqueConstraint("card_id", "helper_id", name="uq_help_card_helper"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id", ondelete="CASCADE"), nullable=False)
    helper_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    card: Mapped[Card] = relationship(back_populates="helps")
    helper: Mapped[User] = relationship(back_populates="helps_given", foreign_keys=[helper_id])


class CardView(Base):
    __tablename__ = "card_views"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id", ondelete="CASCADE"), nullable=False)
    viewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    card: Mapped[Card] = relationship(back_populates="views")


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    amount_label: Mapped[str] = mapped_column(String(64), nullable=False)
    happened_at: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), default="in", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship()
