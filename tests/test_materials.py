"""CRUD de materiais: criar, editar, status (soft delete) e duplicidade de sigla."""

from tests.conftest import auth_headers


def test_cria_material(client, manager_token):
    response = client.post("/materials", json={"code": "pead", "name": "Polietileno de alta densidade", "density": 0.95}, headers=auth_headers(manager_token))

    assert response.status_code == 201
    # A sigla é guardada em maiúsculo.
    assert response.json()["code"] == "PEAD"


def test_sigla_duplicada_eh_rejeitada(client, manager_token):
    client.post("/materials", json={"code": "PP", "name": "Polipropileno", "density": 0.9}, headers=auth_headers(manager_token))

    response = client.post("/materials", json={"code": "pp", "name": "Outro nome", "density": 0.91}, headers=auth_headers(manager_token))

    assert response.status_code == 409


def test_edita_material(client, manager_token):
    created = client.post("/materials", json={"code": "PP", "name": "Polipropileno", "density": 0.9}, headers=auth_headers(manager_token))
    material_id = created.json()["id"]

    response = client.put(f"/materials/{material_id}", json={"code": "PP", "name": "Polipropileno homopolímero", "density": 0.905}, headers=auth_headers(manager_token))

    assert response.status_code == 200
    assert response.json()["name"] == "Polipropileno homopolímero"


def test_muda_status_para_desativado_e_depois_apagado(client, manager_token):
    created = client.post("/materials", json={"code": "PP", "name": "Polipropileno", "density": 0.9}, headers=auth_headers(manager_token))
    material_id = created.json()["id"]

    disable = client.patch(f"/materials/{material_id}/status?new_status=disable", headers=auth_headers(manager_token))
    assert disable.status_code == 200
    assert disable.json()["status"] == "disable"

    delete = client.patch(f"/materials/{material_id}/status?new_status=deleted", headers=auth_headers(manager_token))
    assert delete.status_code == 200
    assert delete.json()["status"] == "deleted"
