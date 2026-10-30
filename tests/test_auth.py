"""Login: sucesso, senha errada e usuário desativado."""

from core import config
from tests.conftest import auth_headers


def test_login_com_senha_correta_devolve_token(client):
    response = client.post("/auth/login", json={"email": config.ADMIN_EMAIL, "password": config.ADMIN_PASSWORD})

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_com_senha_errada_eh_rejeitado(client):
    response = client.post("/auth/login", json={"email": config.ADMIN_EMAIL, "password": "senha-errada"})

    assert response.status_code == 401


def test_login_com_email_inexistente_devolve_a_mesma_mensagem_de_senha_errada(client):
    """Não revela quais e-mails existem: a mensagem é igual para e-mail ou senha errados."""
    resposta_email_errado = client.post("/auth/login", json={"email": "ninguem@teste.com", "password": "qualquer"})
    resposta_senha_errada = client.post("/auth/login", json={"email": config.ADMIN_EMAIL, "password": "qualquer"})

    assert resposta_email_errado.status_code == resposta_senha_errada.status_code == 401
    assert resposta_email_errado.json()["detail"] == resposta_senha_errada.json()["detail"]


def test_usuario_desativado_nao_consegue_logar(client, manager_token):
    create = client.post(
        "/users",
        json={"name": "Desativado", "email": "desativado@teste.com", "password": "senha12345", "role": "funcionario"},
        headers=auth_headers(manager_token),
    )
    user_id = create.json()["id"]
    client.patch(f"/users/{user_id}/status?new_status=disable", headers=auth_headers(manager_token))

    response = client.post("/auth/login", json={"email": "desativado@teste.com", "password": "senha12345"})

    assert response.status_code == 403


def test_rota_protegida_sem_token_eh_rejeitada(client):
    response = client.get("/users/me")

    assert response.status_code == 401
