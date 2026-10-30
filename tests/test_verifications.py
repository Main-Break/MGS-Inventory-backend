"""
Verificações: sem modelo de IA treinado o envio de foto responde 503 (esse é
o comportamento esperado no MVP, documentado em docs/pendencias.md), e a
listagem respeita a permissão verifications.view_all.
"""

import io

from core import verifications as data_verifications
from tests.conftest import auth_headers


def test_envio_de_foto_sem_modelo_treinado_responde_503(client, manager_token):
    photo = io.BytesIO(b"conteudo-fake-de-imagem")

    response = client.post("/verifications", files={"file": ("foto.jpg", photo, "image/jpeg")}, headers=auth_headers(manager_token))

    assert response.status_code == 503


def test_extensao_invalida_eh_rejeitada(client, manager_token):
    photo = io.BytesIO(b"nao e uma imagem")

    response = client.post("/verifications", files={"file": ("arquivo.txt", photo, "text/plain")}, headers=auth_headers(manager_token))

    assert response.status_code == 400


def test_funcionario_ve_apenas_as_propias_verificacoes(client, manager_token, employee_token):
    manager_id = client.get("/users/me", headers=auth_headers(manager_token)).json()["id"]
    employee_id = client.get("/users/me", headers=auth_headers(employee_token)).json()["id"]

    data_verifications.create(manager_id, None, "foto-gestor.jpg", "[]")
    data_verifications.create(employee_id, None, "foto-funcionario.jpg", "[]")

    response = client.get("/verifications", headers=auth_headers(employee_token))

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["photo_filename"] == "foto-funcionario.jpg"


def test_funcionario_com_view_all_ve_todas(client, manager_token, employee_token):
    manager_id = client.get("/users/me", headers=auth_headers(manager_token)).json()["id"]
    employee_id = client.get("/users/me", headers=auth_headers(employee_token)).json()["id"]
    data_verifications.create(manager_id, None, "foto-gestor.jpg", "[]")
    data_verifications.create(employee_id, None, "foto-funcionario.jpg", "[]")

    client.post(f"/users/{employee_id}/permissions/verifications.view_all", headers=auth_headers(manager_token))

    response = client.get("/verifications", headers=auth_headers(employee_token))

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_aprovar_verificacao_exige_permissao(client, manager_token, employee_token):
    employee_id = client.get("/users/me", headers=auth_headers(employee_token)).json()["id"]
    _, created = data_verifications.create(employee_id, None, "foto.jpg", "[]")

    sem_permissao = client.patch(f"/verifications/{created['id']}/approve?approved=true", headers=auth_headers(employee_token))
    assert sem_permissao.status_code == 403

    com_permissao = client.patch(f"/verifications/{created['id']}/approve?approved=true", headers=auth_headers(manager_token))
    assert com_permissao.status_code == 200
    assert com_permissao.json()["approved"] is True
