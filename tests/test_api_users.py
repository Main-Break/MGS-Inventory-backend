"""Testa as rotas de /users, incluindo a regra de acesso (só gestor cria/lista)."""

from fastapi.testclient import TestClient


def test_gestor_cria_usuario(client: TestClient, cabecalho_gestor: dict):
    resposta = client.post(
        "/users",
        json={"name": "Ana", "email": "ana@exemplo.com", "password": "senha1234", "role": "funcionario"},
        headers=cabecalho_gestor,
    )

    assert resposta.status_code == 201
    assert resposta.json()["email"] == "ana@exemplo.com"


def test_nao_deixa_duplicar_email(client: TestClient, cabecalho_gestor: dict):
    dados = {"name": "Ana", "email": "ana@exemplo.com", "password": "senha1234", "role": "funcionario"}
    client.post("/users", json=dados, headers=cabecalho_gestor)

    resposta = client.post("/users", json=dados, headers=cabecalho_gestor)

    assert resposta.status_code == 409


def test_sem_token_nao_cria_usuario(client: TestClient):
    resposta = client.post(
        "/users", json={"name": "Ana", "email": "ana@exemplo.com", "password": "senha1234"}
    )

    assert resposta.status_code == 401


def test_funcionario_nao_pode_criar_usuario(client: TestClient, cabecalho_gestor: dict):
    client.post(
        "/users",
        json={"name": "Ana", "email": "ana@exemplo.com", "password": "senha1234", "role": "funcionario"},
        headers=cabecalho_gestor,
    )
    login = client.post("/auth/login", json={"email": "ana@exemplo.com", "password": "senha1234"})
    cabecalho_funcionario = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resposta = client.post(
        "/users",
        json={"name": "Outro", "email": "outro@exemplo.com", "password": "senha1234"},
        headers=cabecalho_funcionario,
    )

    assert resposta.status_code == 403


def test_meus_dados_retorna_usuario_logado(client: TestClient, cabecalho_gestor: dict):
    resposta = client.get("/users/me", headers=cabecalho_gestor)

    assert resposta.status_code == 200
    assert resposta.json()["role"] == "gestor"
