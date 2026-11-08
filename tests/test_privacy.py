import re

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.headers import SecurityHeadersMiddleware
from app.core.validators import normalize_phone, normalize_requisites
from app.database import db_core
from app.database.crud.cards import upgrade_legacy_public_ids

PASSWORD = "correct-horse-battery"
CARD_NUMBER = "4111 1111 1111 1111"  # тестовый номер, проходит проверку Луна


def register(client, username, name="Alice Doe"):
    resp = client.post("/api/auth/register", json={"name": name, "username": username, "password": PASSWORD})
    assert resp.status_code == 201, resp.text


def login(client, username):
    client.cookies.clear()
    resp = client.post("/api/auth/login", json={"username": username, "password": PASSWORD})
    assert resp.status_code == 200, resp.text


def fill_profile(client, name="Alice Doe"):
    resp = client.put(
        "/api/profile",
        json={"name": name, "phone": "+7 (999) 123-45-67", "bank": "Test Bank", "requisites": CARD_NUMBER},
    )
    assert resp.status_code == 200, resp.text


def make_author(client, username, name="Alice Doe"):
    """Регистрирует пользователя с заполненным профилем и одной карточкой, возвращает id карточки."""
    register(client, username, name)
    fill_profile(client, name)
    resp = client.post("/api/cards", json={"amount": 1000, "purpose": "Нужна помощь с лекарствами", "category": "Other"})
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ---------- 1. защита реквизитов от сбора ----------

def test_public_id_is_long_and_random(client):
    card_id = make_author(client, "alice")
    assert re.fullmatch(r"PD-[A-Z2-9]{10}", card_id)


def test_legacy_short_ids_are_reissued(client):
    card_id = make_author(client, "alice")
    with db_core.SessionLocal() as db:
        from app.database.models import Card

        card = db.query(Card).one()
        card.public_id = "PD-12345"
        db.commit()
        assert upgrade_legacy_public_ids(db) == 1
        db.refresh(card)
        assert card.public_id != "PD-12345"
        assert re.fullmatch(r"PD-[A-Z2-9]{10}", card.public_id)
        assert upgrade_legacy_public_ids(db) == 0
    assert card_id != "PD-12345"


def test_daily_limit_on_revealing_requisites(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "help_daily_limit", 2)
    ids = [make_author(client, f"author{i}", name=f"Author Number{i}") for i in range(3)]
    register(client, "helper", name="Helper Person")
    assert client.post(f"/api/cards/{ids[0]}/help").status_code == 200
    assert client.post(f"/api/cards/{ids[1]}/help").status_code == 200
    blocked = client.post(f"/api/cards/{ids[2]}/help")
    assert blocked.status_code == 429
    assert "bank" not in blocked.json()
    # уже открытые реквизиты по-прежнему доступны и лимит не тратят
    again = client.post(f"/api/cards/{ids[0]}/help")
    assert again.status_code == 200
    assert again.json()["requisites"] == CARD_NUMBER


def test_guessing_card_ids_gets_blocked(client):
    make_author(client, "alice")
    register(client, "scraper", name="Scraper Person")
    codes = [client.post(f"/api/cards/PD-{i:05d}/help").status_code for i in range(31)]
    assert codes[:30] == [404] * 30
    assert codes[30] == 429
    assert client.post("/api/cards/PD-99999/view").status_code == 429


# ---------- 3. выгрузка и удаление данных ----------

def test_export_contains_own_data_only(client):
    card_id = make_author(client, "alice")
    register(client, "bobby", name="Bobby Roe")
    client.post(f"/api/cards/{card_id}/help")
    login(client, "alice")
    resp = client.get("/api/profile/export")
    assert resp.status_code == 200
    assert "attachment" in resp.headers["content-disposition"]
    data = resp.json()
    assert data["profile"]["username"] == "alice"
    assert data["profile"]["requisites"] == CARD_NUMBER
    assert data["profile"]["phone"] == "+79991234567"
    assert [c["id"] for c in data["cards"]] == [card_id]
    assert data["helps_received_count"] == 1
    assert "Bobby" not in resp.text and "bobby" not in resp.text
    assert "password" not in resp.text


def test_export_requires_login(client):
    assert client.get("/api/profile/export").status_code == 401


def test_delete_account_removes_everything(client):
    card_id = make_author(client, "alice")
    register(client, "bobby", name="Bobby Roe")
    client.post(f"/api/cards/{card_id}/help")
    login(client, "alice")

    wrong = client.request("DELETE", "/api/profile", json={"password": "not-the-password"})
    assert wrong.status_code == 401
    assert client.get("/api/profile").status_code == 200  # аккаунт на месте

    ok = client.request("DELETE", "/api/profile", json={"password": PASSWORD})
    assert ok.status_code == 200
    assert client.get("/api/profile").status_code == 401
    bad_login = client.post("/api/auth/login", json={"username": "alice", "password": PASSWORD})
    assert bad_login.status_code == 401

    from app.database.models import Activity, Card, Help, User

    with db_core.SessionLocal() as db:
        assert db.query(User).filter_by(username="alice").count() == 0
        assert db.query(Card).count() == 0
        assert db.query(Help).count() == 0
        titles = [a.title for a in db.query(Activity).all()]
    assert not any("Alice" in t for t in titles)
    assert any("удалённому пользователю" in t for t in titles)

    login(client, "bobby")
    assert client.get("/api/cards").json() == []


def test_delete_account_password_is_rate_limited(client):
    register(client, "alice")
    codes = [client.request("DELETE", "/api/profile", json={"password": f"wrong-{i}"}).status_code for i in range(6)]
    assert codes[:5] == [401] * 5 and codes[5] == 429
    assert client.get("/api/profile").status_code == 200


def test_delete_account_blocked_from_foreign_origin(client):
    register(client, "alice")
    resp = client.request(
        "DELETE", "/api/profile", json={"password": PASSWORD}, headers={"Origin": "https://evil.example"}
    )
    assert resp.status_code == 403
    assert client.get("/api/profile").status_code == 200


# ---------- 4. формат реквизитов и заголовки ----------

def test_phone_normalization():
    assert normalize_phone("+7 (999) 123-45-67") == "+79991234567"
    assert normalize_phone("89991234567") == "89991234567"
    for bad in ["abc", "123", "+7 999 http://evil", "1" * 16]:
        with pytest.raises(ValueError):
            normalize_phone(bad)


def test_requisites_validation():
    assert normalize_requisites("4111111111111111") == "4111 1111 1111 1111"
    assert normalize_requisites("4111-1111-1111-1111") == "4111 1111 1111 1111"
    assert normalize_requisites("+7 999 123 45 67") == "+79991234567"
    assert normalize_requisites("89991234567") == "89991234567"
    assert normalize_requisites("40817810099910004312") == "40817810099910004312"
    for bad in ["https://evil.example/pay", "карта сбербанка", "4111 1111 1111 1112", "12345", "<script>alert(1)</script>"]:
        with pytest.raises(ValueError):
            normalize_requisites(bad)


def test_profile_rejects_junk_and_stores_normalized(client):
    register(client, "alice")
    base = {"name": "Alice Doe", "phone": "+79991234567", "bank": "Test Bank"}
    junk = client.put("/api/profile", json={**base, "requisites": "https://evil.example/pay"})
    assert junk.status_code == 422
    bad_phone = client.put("/api/profile", json={**base, "phone": "call me", "requisites": CARD_NUMBER})
    assert bad_phone.status_code == 422
    ok = client.put("/api/profile", json={**base, "requisites": "4111111111111111"})
    assert ok.status_code == 200
    assert ok.json()["requisites"] == CARD_NUMBER


def test_security_headers():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/data")
    def data() -> dict:
        return {"ok": True}

    https = TestClient(app, base_url="https://testserver").get("/data")
    assert https.headers["x-content-type-options"] == "nosniff"
    assert https.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in https.headers["content-security-policy"]
    assert https.headers["cache-control"] == "no-store"
    assert "max-age" in https.headers["strict-transport-security"]
    plain = TestClient(app, base_url="http://testserver").get("/data")
    assert "strict-transport-security" not in plain.headers
