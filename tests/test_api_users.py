"""Testa as rotas de /users, incluindo a regra de acesso (só gestor cria/lista)."""

from fastapi.testclient import TestClient


def test_manager_creates_user(client: TestClient, manager_header: dict):
    resposta = client.post(
        "/users",
        json={"name": "Ana", "email": "ana@exemplo.com", "password": "senha1234", "role": "funcionario"},
        headers=manager_header,
    )

    assert resposta.status_code == 201
    assert resposta.json()["email"] == "ana@exemplo.com"


def test_does_not_allow_duplicate_email(client: TestClient, manager_header: dict):
    dados = {"name": "Ana", "email": "ana@exemplo.com", "password": "senha1234", "role": "funcionario"}
    client.post("/users", json=dados, headers=manager_header)

    resposta = client.post("/users", json=dados, headers=manager_header)

    assert resposta.status_code == 409


def test_without_token_cannot_create_user(client: TestClient):
    resposta = client.post(
        "/users", json={"name": "Ana", "email": "ana@exemplo.com", "password": "senha1234"}
    )

    assert resposta.status_code == 401


def test_employee_cannot_create_user(client: TestClient, manager_header: dict):
    client.post(
        "/users",
        json={"name": "Ana", "email": "ana@exemplo.com", "password": "senha1234", "role": "funcionario"},
        headers=manager_header,
    )
    login = client.post("/auth/login", json={"email": "ana@exemplo.com", "password": "senha1234"})
    employee_header = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resposta = client.post(
        "/users",
        json={"name": "Outro", "email": "outro@exemplo.com", "password": "senha1234"},
        headers=employee_header,
    )

    assert resposta.status_code == 403


def test_my_profile_returns_logged_in_user(client: TestClient, manager_header: dict):
    resposta = client.get("/users/me", headers=manager_header)

    assert resposta.status_code == 200
    assert resposta.json()["role"] == "gestor"
