from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_menu(client: TestClient) -> None:
    response = client.get("/api/menu")
    payload = response.json()
    assert payload["items"][0]["id"] == "feed"
    assert "Т-Банк" in payload["banks"]
    assert payload["colors"]["Техника"] == "#D9F99D"


def test_cards_hide_requisites(client: TestClient) -> None:
    cards = client.get("/api/cards").json()
    assert len(cards) >= 4
    assert cards[0]["id"].startswith("PD-")
    assert "requisites" not in cards[0]


def test_feed_excludes_own_cards(client: TestClient) -> None:
    ids = {card["id"] for card in client.get("/api/cards").json()}
    assert "PD-24081" in ids
    assert "PD-11021" not in ids
    assert "PD-11022" not in ids


def test_help_returns_requisites(client: TestClient) -> None:
    cards = client.get("/api/cards").json()
    public_id = cards[0]["id"]
    response = client.post(f"/api/cards/{public_id}/help")
    assert response.status_code == 200
    body = response.json()
    assert body["requisites"]
    assert body["bank"]


def test_help_is_idempotent(client: TestClient) -> None:
    public_id = client.get("/api/cards").json()[0]["id"]
    first = client.post(f"/api/cards/{public_id}/help")
    second = client.post(f"/api/cards/{public_id}/help")
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["requisites"] == second.json()["requisites"]


def test_cannot_help_own_card(client: TestClient) -> None:
    created = client.post(
        "/api/cards",
        json={
            "amount": 4100,
            "purpose": "Сбор на канцтовары и доступ к учебным материалам",
            "category": "Образование",
        },
    )
    assert created.status_code == 201
    response = client.post(f"/api/cards/{created.json()['id']}/help")
    assert response.status_code == 400


def test_create_card_validation(client: TestClient) -> None:
    response = client.post("/api/cards", json={"amount": 0, "purpose": "short", "category": "Образование"})
    assert response.status_code == 422


def test_create_card(client: TestClient) -> None:
    response = client.post(
        "/api/cards",
        json={
            "amount": 5000,
            "purpose": "Нужны деньги на оплату учебного курса по дизайну",
            "category": "Образование",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["amount"] == 5000
    assert body["author"] == "Алексей Морозов"


def test_update_profile(client: TestClient) -> None:
    response = client.put(
        "/api/profile",
        json={
            "name": "Алексей Морозов",
            "phone": "+7 999 111-22-33",
            "bank": "Сбер",
            "requisites": "+7 999 111-22-33",
        },
    )
    assert response.status_code == 200
    assert response.json()["bank"] == "Сбер"
    assert response.json()["phone"] == "+7 999 111-22-33"


def test_stats_from_database(client: TestClient) -> None:
    stats = client.get("/api/stats").json()
    assert stats["collected"] == 24650
    assert stats["helped_people"] == 12
    assert stats["helped_amount"] == 8400
    assert len(stats["chart"]) == 7
    assert stats["collected_delta"]


def test_stats_period_filters_amounts(client: TestClient) -> None:
    month = client.get("/api/stats?period=month").json()
    week = client.get("/api/stats?period=week").json()
    assert month["collected"] == 24650
    assert week["collected"] < month["collected"]
    assert week["collected"] == 13200


def test_admin_requires_token(client: TestClient) -> None:
    response = client.get("/api/admin/cards")
    assert response.status_code == 401


def test_admin_login_and_toggle(client: TestClient) -> None:
    login = client.post("/api/admin/login", json={"password": "change-me"})
    assert login.status_code == 200
    token = login.json()["token"]
    cards = client.get("/api/admin/cards", headers={"X-Admin-Token": token}).json()
    card_id = cards[0]["id"]
    toggled = client.post(f"/api/admin/cards/{card_id}/toggle", headers={"X-Admin-Token": token})
    assert toggled.status_code == 200
    assert "is_active" in toggled.json()
