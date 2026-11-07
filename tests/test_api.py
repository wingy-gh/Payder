from fastapi.testclient import TestClient


def register(client: TestClient, username: str = "firstuser", name: str = "Первый Пользователь") -> None:
    response = client.post("/api/auth/register", json={
        "name": name, "username": username, "password": "safe-pass-123"
    })
    assert response.status_code == 201, response.text


def test_health(client: TestClient) -> None:
    assert client.get("/api/health").json()["status"] == "ok"


def test_auth_required(client: TestClient) -> None:
    assert client.get("/api/profile").status_code == 401
    assert client.get("/api/cards").status_code == 401


def test_register_login_logout(client: TestClient) -> None:
    register(client)
    assert client.get("/api/profile").json()["username"] == "firstuser"
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/profile").status_code == 401
    login = client.post("/api/auth/login", json={"username": "firstuser", "password": "safe-pass-123"})
    assert login.status_code == 200
    assert client.get("/api/profile").status_code == 200


def test_duplicate_username_and_bad_password(client: TestClient) -> None:
    register(client)
    duplicate = client.post("/api/auth/register", json={
        "name": "Другой", "username": "FIRSTUSER", "password": "safe-pass-123"
    })
    assert duplicate.status_code == 409
    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={
        "username": "firstuser", "password": "wrong-pass-123"
    }).status_code == 401


def test_new_database_has_no_demo_cards(client: TestClient) -> None:
    register(client)
    assert client.get("/api/cards").json() == []


def test_cards_are_shared_between_accounts(client: TestClient) -> None:
    register(client, "creator", "Создатель Карточки")
    created = client.post("/api/cards", json={
        "amount": 5000,
        "purpose": "Нужны средства на учебный курс программирования",
        "category": "Образование",
    })
    assert created.status_code == 201
    public_id = created.json()["id"]

    client.post("/api/auth/logout")
    register(client, "viewer", "Другой Пользователь")
    feed = client.get("/api/cards").json()
    assert any(card["id"] == public_id and card["author"] == "Создатель Карточки" for card in feed)
    assert all("requisites" not in card for card in feed)


def test_own_cards_are_not_in_own_feed(client: TestClient) -> None:
    register(client)
    client.post("/api/cards", json={
        "amount": 5000,
        "purpose": "Нужны средства на учебный курс программирования",
        "category": "Образование",
    })
    assert client.get("/api/cards").json() == []


def test_create_card_validation(client: TestClient) -> None:
    register(client)
    response = client.post("/api/cards", json={"amount": 0, "purpose": "short", "category": "Образование"})
    assert response.status_code == 422


def test_profile_update(client: TestClient) -> None:
    register(client)
    response = client.put("/api/profile", json={
        "name": "Первый Пользователь", "phone": "+7 999 111-22-33",
        "bank": "Сбер", "requisites": "+7 999 111-22-33",
    })
    assert response.status_code == 200
    assert response.json()["bank"] == "Сбер"


def test_menu(client: TestClient) -> None:
    payload = client.get("/api/menu").json()
    assert payload["items"][0]["id"] == "feed"
    assert "Т-Банк" in payload["banks"]
    assert payload["colors"]["Техника"] == "#D9F99D"


def test_requisites_only_after_help(client: TestClient) -> None:
    register(client, "author", "Автор Карточки")
    client.put("/api/profile", json={
        "name": "Автор Карточки", "phone": "+7 900 111-22-33",
        "bank": "Сбер", "requisites": "+7 900 111-22-33",
    })
    created = client.post("/api/cards", json={
        "amount": 5000, "purpose": "Нужны средства на учебный курс программирования",
        "category": "Образование",
    }).json()
    client.post("/api/auth/logout")
    register(client, "supporter", "Тот Кто Помогает")
    feed = client.get("/api/cards").json()
    assert "requisites" not in feed[0]
    helped = client.post(f"/api/cards/{created['id']}/help")
    assert helped.status_code == 200
    assert helped.json()["requisites"] == "+7 900 111-22-33"


def test_stats_for_new_account(client: TestClient) -> None:
    register(client)
    response = client.get("/api/stats")
    assert response.status_code == 200
    assert response.json()["collected"] == 0
