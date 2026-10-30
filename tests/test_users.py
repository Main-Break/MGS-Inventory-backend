"""Usuários: criar, listar com busca, perfil próprio (/me) e troca de status."""

from tests.conftest import auth_headers


def test_cria_funcionario(client, manager_token):
    response = client.post(
        "/users",
        json={"name": "Novo Funcionário", "email": "novo@teste.com", "password": "senha12345", "role": "funcionario"},
        headers=auth_headers(manager_token),
    )

    assert response.status_code == 201
    assert response.json()["role"] == "funcionario"


def test_email_duplicado_eh_rejeitado(client, manager_token):
    client.post("/users", json={"name": "A", "email": "repetido@teste.com", "password": "senha12345"}, headers=auth_headers(manager_token))

    response = client.post("/users", json={"name": "B", "email": "repetido@teste.com", "password": "senha12345"}, headers=auth_headers(manager_token))

    assert response.status_code == 409


def test_lista_usuarios_com_busca(client, manager_token):
    client.post("/users", json={"name": "Maria Silva", "email": "maria@teste.com", "password": "senha12345"}, headers=auth_headers(manager_token))
    client.post("/users", json={"name": "João Souza", "email": "joao@teste.com", "password": "senha12345"}, headers=auth_headers(manager_token))

    response = client.get("/users?q=maria", headers=auth_headers(manager_token))

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Maria Silva"


def test_meu_perfil_traz_as_permissoes(client, employee_token):
    response = client.get("/users/me", headers=auth_headers(employee_token))

    assert response.status_code == 200
    assert response.json()["permissions"] == []


def test_atualiza_meu_perfil(client, employee_token):
    response = client.put("/users/me", json={"name": "Nome Novo", "email": "funcionario@teste.com"}, headers=auth_headers(employee_token))

    assert response.status_code == 200
    assert response.json()["name"] == "Nome Novo"


def test_gestor_desativa_funcionario(client, manager_token, employee_token):
    employee_id = client.get("/users/me", headers=auth_headers(employee_token)).json()["id"]

    response = client.patch(f"/users/{employee_id}/status?new_status=disable", headers=auth_headers(manager_token))

    assert response.status_code == 200
    assert response.json()["status"] == "disable"


def test_funcionario_nao_pode_desativar_gestor(client, manager_token, employee_token):
    manager_id = client.get("/users/me", headers=auth_headers(manager_token)).json()["id"]
    employee_id = client.get("/users/me", headers=auth_headers(employee_token)).json()["id"]
    client.post(f"/users/{employee_id}/permissions/users.status", headers=auth_headers(manager_token))

    response = client.patch(f"/users/{manager_id}/status?new_status=disable", headers=auth_headers(employee_token))

    assert response.status_code == 403
