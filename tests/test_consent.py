from app.core.legal import LEGAL_VERSION

PASSWORD = "safe-pass-123"


def _register(client, username="consentuser", **extra):
    return client.post(
        "/api/auth/register",
        json={"name": "Пользователь Тест", "username": username, "password": PASSWORD, **extra},
    )


def test_registration_with_consent_records_documents(client):
    assert _register(client, consent_version=LEGAL_VERSION).status_code == 201
    assert client.get("/api/profile").json()["legal_accepted"] is True
    export = client.get("/api/profile/export").json()
    assert {item["document"] for item in export["consents"]} == {"terms", "privacy"}
    assert all(item["version"] == LEGAL_VERSION and item["accepted_at"] for item in export["consents"])


def test_registration_rejects_outdated_documents_version(client):
    assert _register(client, consent_version="0.0").status_code == 409
    assert client.get("/api/profile").status_code == 401


def test_user_without_consent_is_asked_and_can_accept(client):
    assert _register(client).status_code == 201
    assert client.get("/api/profile").json()["legal_accepted"] is False
    assert client.post("/api/profile/consent", json={"version": "0.0"}).status_code == 409
    accepted = client.post("/api/profile/consent", json={"version": LEGAL_VERSION})
    assert accepted.status_code == 200
    assert accepted.json()["legal_accepted"] is True
    # повторное принятие не создаёт дубликаты
    client.post("/api/profile/consent", json={"version": LEGAL_VERSION})
    assert len(client.get("/api/profile/export").json()["consents"]) == 2


def test_consent_requires_login(client):
    assert client.post("/api/profile/consent", json={"version": LEGAL_VERSION}).status_code == 401
