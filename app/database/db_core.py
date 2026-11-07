from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


engine: Engine | None = None
SessionLocal: sessionmaker | None = None


def _ensure_sqlite_path(url: str) -> None:
    if not url.startswith("sqlite:///"):
        return
    raw = url.replace("sqlite:///", "", 1)
    if raw in {":memory:", ""}:
        return
    db_path = Path(raw)
    if db_path.parent and not db_path.parent.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)


def configure_engine(database_url: str | None = None) -> Engine:
    global engine, SessionLocal
    url = database_url or get_settings().database_url
    _ensure_sqlite_path(url)
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args, future=True)
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return engine


def get_db() -> Generator[Session, None, None]:
    if SessionLocal is None:
        configure_engine()
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db(database_url: str | None = None) -> None:
    from app.database import models  # noqa: F401
    from app.core.seed import seed_if_empty

    configure_engine(database_url)
    assert engine is not None and SessionLocal is not None

    # Lightweight forward migration for databases created by older Payder versions.
    # create_all() creates missing tables but does not add columns to existing ones.
    if engine.dialect.name == "sqlite":
        inspector = inspect(engine)
        if "users" in inspector.get_table_names():
            user_columns = {column["name"] for column in inspector.get_columns("users")}
            if "password_hash" not in user_columns:
                with engine.begin() as connection:
                    connection.execute(
                        text(
                            "ALTER TABLE users "
                            "ADD COLUMN password_hash VARCHAR(256) NOT NULL DEFAULT ''"
                        )
                    )

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
