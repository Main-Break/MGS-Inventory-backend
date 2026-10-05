"""Testa /auth/login de ponta a ponta, passando pela API de verdade."""

import config
from fastapi.testclient import TestClient


def test_initial_manager_login_works(client: TestClient):
    resposta = client.post("/auth/login", json={"email": config.ADMIN_EMAIL, "password": config.ADMIN_PASSWORD})

    assert resposta.status_code == 200
    assert resposta.json()["token_type"] == "bearer"
    assert resposta.json()["access_token"]


def test_login_with_wrong_password_fails(client: TestClient):
    resposta = client.post("/auth/login", json={"email": config.ADMIN_EMAIL, "password": "senha-errada"})

    assert resposta.status_code == 401


def test_login_with_unknown_email_fails(client: TestClient):
    resposta = client.post("/auth/login", json={"email": "ninguem@exemplo.com", "password": "qualquer"})

    assert resposta.status_code == 401
