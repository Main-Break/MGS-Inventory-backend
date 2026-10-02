"""Testa /auth/login de ponta a ponta, passando pela API de verdade."""

import core
from fastapi.testclient import TestClient


def test_login_do_gestor_inicial_funciona(client: TestClient):
    resposta = client.post("/auth/login", json={"email": core.ADMIN_EMAIL, "password": core.ADMIN_PASSWORD})

    assert resposta.status_code == 200
    assert resposta.json()["token_type"] == "bearer"
    assert resposta.json()["access_token"]


def test_login_com_senha_errada_falha(client: TestClient):
    resposta = client.post("/auth/login", json={"email": core.ADMIN_EMAIL, "password": "senha-errada"})

    assert resposta.status_code == 401


def test_login_com_email_inexistente_falha(client: TestClient):
    resposta = client.post("/auth/login", json={"email": "ninguem@exemplo.com", "password": "qualquer"})

    assert resposta.status_code == 401
