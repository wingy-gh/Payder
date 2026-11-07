from pathlib import Path

from sqlalchemy import create_engine, inspect, text

from app.database.db_core import init_db


def test_existing_sqlite_database_gets_password_hash_column(tmp_path: Path) -> None:
    database_path = tmp_path / "legacy.db"
    engine = create_engine(f"sqlite:///{database_path}")
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                username VARCHAR(64) NOT NULL UNIQUE,
                phone VARCHAR(32) NOT NULL DEFAULT '',
                bank VARCHAR(64) NOT NULL DEFAULT '',
                requisites VARCHAR(64) NOT NULL DEFAULT '',
                initials VARCHAR(8) NOT NULL,
                created_at DATETIME
            )
        """))
        connection.execute(text("""
            INSERT INTO users (id, name, username, initials)
            VALUES (1, 'Старый пользователь', 'legacy', 'СП')
        """))
    engine.dispose()

    init_db(f"sqlite:///{database_path}")

    migrated_engine = create_engine(f"sqlite:///{database_path}")
    columns = {column["name"] for column in inspect(migrated_engine).get_columns("users")}
    assert "password_hash" in columns
    with migrated_engine.connect() as connection:
        row = connection.execute(
            text("SELECT username, password_hash FROM users WHERE id = 1")
        ).one()
    assert row.username == "legacy"
    assert row.password_hash == ""
    migrated_engine.dispose()
