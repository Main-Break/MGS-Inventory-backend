"""Testa as rotas de /items."""

from fastapi.testclient import TestClient


def test_manager_creates_item(client: TestClient, manager_header: dict):
    resposta = client.post(
        "/items",
        json={"label": "parafuso_m6", "name": "Parafuso M6", "stock_quantity": 10},
        headers=manager_header,
    )

    assert resposta.status_code == 201
    assert resposta.json()["label"] == "parafuso_m6"


def test_does_not_allow_duplicate_label(client: TestClient, manager_header: dict):
    dados = {"label": "parafuso_m6", "name": "Parafuso M6", "stock_quantity": 10}
    client.post("/items", json=dados, headers=manager_header)

    resposta = client.post("/items", json=dados, headers=manager_header)

    assert resposta.status_code == 409


def test_get_missing_item_returns_404(client: TestClient, manager_header: dict):
    resposta = client.get("/items/999", headers=manager_header)

    assert resposta.status_code == 404


def test_search_items_with_filter(client: TestClient, manager_header: dict):
    client.post(
        "/items", json={"label": "parafuso_m6", "name": "Parafuso M6", "stock_quantity": 10},
        headers=manager_header,
    )
    client.post(
        "/items", json={"label": "porca_m6", "name": "Porca M6", "stock_quantity": 5}, headers=manager_header
    )

    resposta = client.get("/items", params={"q": "parafuso"}, headers=manager_header)

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["label"] == "parafuso_m6"
