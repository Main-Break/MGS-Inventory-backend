"""Testa as rotas de /verifications.

A IA de verdade (YOLO/ultralytics) é pesada e nem sempre está instalada,
então aqui ela é trocada por uma falsa via injeção de dependência do FastAPI.
"""

import io

from fastapi.testclient import TestClient

from main import app
from routes.verifications import _obter_neural


class _NeuralFalsa:
    def contar_itens(self, caminho_imagem):
        return [{"label": "parafuso_m6", "count": 3, "confidence": 0.9}]


def _imagem_fake() -> tuple[str, io.BytesIO, str]:
    return ("foto.jpg", io.BytesIO(b"conteudo-fake-de-imagem"), "image/jpeg")


def test_sem_modelo_treinado_devolve_503(client: TestClient, cabecalho_gestor: dict):
    resposta = client.post("/verifications", files={"file": _imagem_fake()}, headers=cabecalho_gestor)

    assert resposta.status_code == 503


def test_cria_verificacao_com_ia_falsa(client: TestClient, cabecalho_gestor: dict):
    app.dependency_overrides[_obter_neural] = lambda: _NeuralFalsa()
    try:
        resposta = client.post("/verifications", files={"file": _imagem_fake()}, headers=cabecalho_gestor)
    finally:
        app.dependency_overrides.pop(_obter_neural, None)

    assert resposta.status_code == 201
    deteccoes = resposta.json()["detections"]
    assert deteccoes == [{"label": "parafuso_m6", "count": 3, "confidence": 0.9}]


def test_extensao_invalida_devolve_400(client: TestClient, cabecalho_gestor: dict):
    resposta = client.post(
        "/verifications",
        files={"file": ("foto.txt", io.BytesIO(b"nao e imagem"), "text/plain")},
        headers=cabecalho_gestor,
    )

    assert resposta.status_code == 400


def test_funcionario_so_ve_as_proprias_verificacoes(client: TestClient, cabecalho_gestor: dict):
    client.post(
        "/users",
        json={"name": "Ana", "email": "ana@exemplo.com", "password": "senha1234", "role": "funcionario"},
        headers=cabecalho_gestor,
    )
    login = client.post("/auth/login", json={"email": "ana@exemplo.com", "password": "senha1234"})
    cabecalho_funcionario = {"Authorization": f"Bearer {login.json()['access_token']}"}

    app.dependency_overrides[_obter_neural] = lambda: _NeuralFalsa()
    try:
        client.post("/verifications", files={"file": _imagem_fake()}, headers=cabecalho_gestor)
        client.post("/verifications", files={"file": _imagem_fake()}, headers=cabecalho_funcionario)
    finally:
        app.dependency_overrides.pop(_obter_neural, None)

    resposta = client.get("/verifications", headers=cabecalho_funcionario)

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
