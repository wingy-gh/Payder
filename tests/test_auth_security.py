import time

import pytest
from pydantic import ValidationError

from app.core import security
from app.core.config import Settings

PASSWORD = "correct-horse-battery"


def register(client, username="alice"):
    return client.post("/api/auth/register", json={"name": "Alice Doe", "username": username, "password": PASSWORD})


def test_config_rejects_placeholder_and_short_secrets():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, secret_key="replace-with-a-long-random-secret", admin_password="x" * 20)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, secret_key="s" * 40, admin_password="change-me")
    with pytest.raises(ValidationError):
        Settings(_env_file=None, secret_key="short", admin_password="x" * 20)


def test_register_login_and_profile(client):
    assert register(client).status_code == 201
    assert client.get("/api/profile").status_code == 200
    client.cookies.clear()
    assert client.get("/api/profile").status_code == 401
    bad = client.post("/api/auth/login", json={"username": "alice", "password": "wrong-password"})
    assert bad.status_code == 401
    ok = client.post("/api/auth/login", json={"username": "alice", "password": PASSWORD})
    assert ok.status_code == 200
    assert client.get("/api/profile").status_code == 200


def test_logout_revokes_stolen_token(client):
    register(client)
    stolen = client.cookies.get("payder_session")
    assert client.post("/api/auth/logout").status_code == 200
    client.cookies.clear()
    client.cookies.set("payder_session", stolen)
    assert client.get("/api/profile").status_code == 401


def test_legacy_token_without_version_still_works(client):
    import base64, hashlib, hmac, json

    user_id = register(client).json()["id"]
    body = base64.urlsafe_b64encode(
        json.dumps({"sub": user_id, "exp": int(time.time()) + 600}, separators=(",", ":")).encode()
    ).rstrip(b"=")
    key = security.get_settings().secret_key.encode()
    sig = base64.urlsafe_b64encode(hmac.new(key, body, hashlib.sha256).digest()).rstrip(b"=")
    client.cookies.clear()
    client.cookies.set("payder_session", body.decode() + "." + sig.decode())
    assert client.get("/api/profile").status_code == 200


def test_tampered_and_expired_tokens_rejected(client):
    register(client)
    token = client.cookies.get("payder_session")
    client.cookies.clear()
    client.cookies.set("payder_session", token[:-3] + ("AAA" if not token.endswith("AAA") else "BBB"))
    assert client.get("/api/profile").status_code == 401
    assert security._read(security._issue({"sub": 1, "typ": "user"}, -10)) is None


def test_login_bruteforce_is_rate_limited(client):
    register(client)
    client.cookies.clear()
    codes = [
        client.post("/api/auth/login", json={"username": "alice", "password": f"wrong-pass-{i}"}).status_code
        for i in range(6)
    ]
    assert codes[:5] == [401] * 5
    assert codes[5] == 429
    # даже правильный пароль после блокировки не проходит
    assert client.post("/api/auth/login", json={"username": "alice", "password": PASSWORD}).status_code == 429


def test_successful_login_resets_counter(client):
    register(client)
    client.cookies.clear()
    for i in range(4):
        client.post("/api/auth/login", json={"username": "alice", "password": f"wrong-pass-{i}"})
    assert client.post("/api/auth/login", json={"username": "alice", "password": PASSWORD}).status_code == 200
    for i in range(4):
        assert client.post("/api/auth/login", json={"username": "alice", "password": f"wrong-pass-{i}"}).status_code == 401


def test_registration_is_rate_limited_and_rejects_weak_passwords(client):
    weak = client.post("/api/auth/register", json={"name": "Bob Roe", "username": "bobby", "password": "password123"})
    assert weak.status_code == 422
    same = client.post("/api/auth/register", json={"name": "Bob Roe", "username": "bobbyboby", "password": "bobbyboby"})
    assert same.status_code == 422
    codes = [register(client, f"user{i}").status_code for i in range(11)]
    assert codes[-1] == 429


def test_csrf_blocks_foreign_origin_but_allows_same_origin(client):
    register(client)
    foreign = client.post("/api/auth/logout", headers={"Origin": "https://evil.example"})
    assert foreign.status_code == 403
    assert client.get("/api/profile").status_code == 200  # сессия не тронута
    same = client.post("/api/auth/logout", headers={"Origin": "http://testserver"})
    assert same.status_code == 200


def test_admin_token_is_not_the_password(client):
    resp = client.post("/admin/login", json={"password": "test-admin-password-123"})
    assert resp.status_code == 200
    token = resp.json()["token"]
    assert token != "test-admin-password-123"
    assert client.get("/admin/users", headers={"X-Admin-Token": token}).status_code == 200
    # сам пароль в роли токена больше не работает
    assert client.get("/admin/users", headers={"X-Admin-Token": "test-admin-password-123"}).status_code == 401
    assert client.get("/admin/users").status_code == 401


def test_admin_wrong_password_and_lockout(client):
    codes = [client.post("/admin/login", json={"password": f"nope-{i}"}).status_code for i in range(6)]
    assert codes[:5] == [401] * 5 and codes[5] == 429
    assert client.post("/admin/login", json={"password": "test-admin-password-123"}).status_code == 429


def test_admin_login_validates_payload(client):
    assert client.post("/admin/login", json={}).status_code == 422
    assert client.post("/admin/login", json={"password": ["x"]}).status_code == 422


def test_user_and_admin_tokens_are_not_interchangeable(client):
    register(client)
    user_token = client.cookies.get("payder_session")
    assert client.get("/admin/users", headers={"X-Admin-Token": user_token}).status_code == 401
    admin_token = security.create_admin_token()
    client.cookies.clear()
    client.cookies.set("payder_session", admin_token)
    assert client.get("/api/profile").status_code == 401


def test_migration_adds_token_version_to_old_database(tmp_path):
    import sqlite3
    from app.database import db_core

    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, name VARCHAR(120) NOT NULL, username VARCHAR(64) NOT NULL UNIQUE,"
        " password_hash VARCHAR(256) NOT NULL, phone VARCHAR(32) NOT NULL DEFAULT '', bank VARCHAR(64) NOT NULL DEFAULT '',"
        " requisites VARCHAR(64) NOT NULL DEFAULT '', initials VARCHAR(8) NOT NULL, created_at DATETIME)"
    )
    conn.execute("INSERT INTO users (name, username, password_hash, initials) VALUES ('Old User', 'old', 'x', 'OU')")
    conn.commit()
    conn.close()
    db_core.init_db(f"sqlite:///{path}")
    conn = sqlite3.connect(path)
    assert conn.execute("SELECT token_version FROM users").fetchone() == (0,)
    conn.close()
