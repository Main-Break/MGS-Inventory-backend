"""Testa as rotas de /verifications.

A IA de verdade (YOLO/ultralytics) é pesada e nem sempre está instalada,
então aqui ela é trocada por uma falsa via injeção de dependência do FastAPI.
"""

import io

from fastapi.testclient import TestClient

from main import app
from routes.verifications import _get_neural


class FakeNeural:
    def count_items(self, image_path):
        return [{"label": "parafuso_m6", "count": 3, "confidence": 0.9}]


def _fake_image() -> tuple[str, io.BytesIO, str]:
    return ("foto.jpg", io.BytesIO(b"conteudo-fake-de-imagem"), "image/jpeg")


def test_without_trained_model_returns_503(client: TestClient, manager_header: dict):
    resposta = client.post("/verifications", files={"file": _fake_image()}, headers=manager_header)

    assert resposta.status_code == 503


def test_creates_verification_with_fake_ai(client: TestClient, manager_header: dict):
    app.dependency_overrides[_get_neural] = lambda: FakeNeural()
    try:
        resposta = client.post("/verifications", files={"file": _fake_image()}, headers=manager_header)
    finally:
        app.dependency_overrides.pop(_get_neural, None)

    assert resposta.status_code == 201
    detections = resposta.json()["detections"]
    assert detections == [{"label": "parafuso_m6", "count": 3, "confidence": 0.9}]


def test_invalid_extension_returns_400(client: TestClient, manager_header: dict):
    resposta = client.post(
        "/verifications",
        files={"file": ("foto.txt", io.BytesIO(b"nao e imagem"), "text/plain")},
        headers=manager_header,
    )

    assert resposta.status_code == 400


def test_employee_only_sees_own_verifications(client: TestClient, manager_header: dict):
    client.post(
        "/users",
        json={"name": "Ana", "email": "ana@exemplo.com", "password": "senha1234", "role": "funcionario"},
        headers=manager_header,
    )
    login = client.post("/auth/login", json={"email": "ana@exemplo.com", "password": "senha1234"})
    employee_header = {"Authorization": f"Bearer {login.json()['access_token']}"}

    app.dependency_overrides[_get_neural] = lambda: FakeNeural()
    try:
        client.post("/verifications", files={"file": _fake_image()}, headers=manager_header)
        client.post("/verifications", files={"file": _fake_image()}, headers=employee_header)
    finally:
        app.dependency_overrides.pop(_get_neural, None)

    resposta = client.get("/verifications", headers=employee_header)

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
