"""Permissões: o gestor sempre pode, o funcionário só com a permissão liberada."""

from tests.conftest import auth_headers


def test_funcionario_sem_permissao_recebe_403(client, employee_token):
    response = client.post("/materials", json={"code": "PP", "name": "Polipropileno", "density": 0.9}, headers=auth_headers(employee_token))

    assert response.status_code == 403


def test_gestor_libera_permissao_e_funcionario_passa_a_poder(client, manager_token, employee_token):
    employee_id = client.get("/users/me", headers=auth_headers(employee_token)).json()["id"]

    grant = client.post(f"/users/{employee_id}/permissions/materials.create", headers=auth_headers(manager_token))
    assert grant.status_code == 200
    assert "materials.create" in grant.json()

    response = client.post("/materials", json={"code": "PP", "name": "Polipropileno", "density": 0.9}, headers=auth_headers(employee_token))
    assert response.status_code == 201


def test_gestor_retira_permissao_e_funcionario_perde_acesso(client, manager_token, employee_token):
    employee_id = client.get("/users/me", headers=auth_headers(employee_token)).json()["id"]
    client.post(f"/users/{employee_id}/permissions/materials.create", headers=auth_headers(manager_token))

    revoke = client.delete(f"/users/{employee_id}/permissions/materials.create", headers=auth_headers(manager_token))
    assert revoke.status_code == 200
    assert "materials.create" not in revoke.json()

    response = client.post("/materials", json={"code": "PP", "name": "Polipropileno", "density": 0.9}, headers=auth_headers(employee_token))
    assert response.status_code == 403


def test_funcionario_nao_pode_liberar_permissao_nem_para_si_mesmo(client, employee_token):
    employee_id = client.get("/users/me", headers=auth_headers(employee_token)).json()["id"]

    response = client.post(f"/users/{employee_id}/permissions/materials.create", headers=auth_headers(employee_token))

    assert response.status_code == 403


def test_funcionario_nao_pode_cadastrar_gestor(client, employee_token):
    response = client.post(
        "/users",
        json={"name": "Outro", "email": "outro@teste.com", "password": "senha12345", "role": "gestor"},
        headers=auth_headers(employee_token),
    )

    assert response.status_code == 403


def test_funcionario_com_permissao_users_create_ainda_nao_pode_cadastrar_gestor(client, manager_token, employee_token):
    employee_id = client.get("/users/me", headers=auth_headers(employee_token)).json()["id"]
    client.post(f"/users/{employee_id}/permissions/users.create", headers=auth_headers(manager_token))

    response = client.post(
        "/users",
        json={"name": "Outro", "email": "outro@teste.com", "password": "senha12345", "role": "gestor"},
        headers=auth_headers(employee_token),
    )

    assert response.status_code == 403
