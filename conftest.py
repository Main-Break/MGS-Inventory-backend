"""Fixtures compartilhadas pelos testes (ver tests/).

Cada teste ganha um banco SQLite novo, num arquivo temporário, pra não
misturar dados entre testes nem com o banco real do projeto.
"""

import pytest
from fastapi.testclient import TestClient

import config
from app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_FILE", str(tmp_path / "teste.db"))
    monkeypatch.setattr(config, "UPLOAD_DIR", tmp_path / "uploads")
    with TestClient(app) as cliente:
        yield cliente


@pytest.fixture
def manager_token(client: TestClient) -> str:
    resposta = client.post("/auth/login", json={"email": config.ADMIN_EMAIL, "password": config.ADMIN_PASSWORD})
    return resposta.json()["access_token"]


@pytest.fixture
def manager_header(manager_token: str) -> dict:
    return {"Authorization": f"Bearer {manager_token}"}
