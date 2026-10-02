"""Testa as rotas de /items."""

from fastapi.testclient import TestClient


def test_gestor_cria_item(client: TestClient, cabecalho_gestor: dict):
    resposta = client.post(
        "/items",
        json={"label": "parafuso_m6", "name": "Parafuso M6", "stock_quantity": 10},
        headers=cabecalho_gestor,
    )

    assert resposta.status_code == 201
    assert resposta.json()["label"] == "parafuso_m6"


def test_nao_deixa_duplicar_label(client: TestClient, cabecalho_gestor: dict):
    dados = {"label": "parafuso_m6", "name": "Parafuso M6", "stock_quantity": 10}
    client.post("/items", json=dados, headers=cabecalho_gestor)

    resposta = client.post("/items", json=dados, headers=cabecalho_gestor)

    assert resposta.status_code == 409


def test_buscar_item_inexistente_retorna_404(client: TestClient, cabecalho_gestor: dict):
    resposta = client.get("/items/999", headers=cabecalho_gestor)

    assert resposta.status_code == 404


def test_listar_itens_com_filtro(client: TestClient, cabecalho_gestor: dict):
    client.post(
        "/items", json={"label": "parafuso_m6", "name": "Parafuso M6", "stock_quantity": 10},
        headers=cabecalho_gestor,
    )
    client.post(
        "/items", json={"label": "porca_m6", "name": "Porca M6", "stock_quantity": 5}, headers=cabecalho_gestor
    )

    resposta = client.get("/items", params={"q": "parafuso"}, headers=cabecalho_gestor)

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["label"] == "parafuso_m6"
