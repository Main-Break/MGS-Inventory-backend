"""CRUD de itens: criar, editar, status (soft delete), label duplicado e material inexistente."""

from tests.conftest import auth_headers


def test_cria_item(client, manager_token):
    response = client.post("/itens", json={"name": "Tampa 500ml", "label": "tampa_500"}, headers=auth_headers(manager_token))

    assert response.status_code == 201
    assert response.json()["label"] == "tampa_500"
    assert response.json()["status"] == "active"


def test_label_duplicado_eh_rejeitado(client, manager_token):
    client.post("/itens", json={"name": "Tampa 500ml", "label": "tampa_500"}, headers=auth_headers(manager_token))

    response = client.post("/itens", json={"name": "Outra tampa", "label": "tampa_500"}, headers=auth_headers(manager_token))

    assert response.status_code == 409


def test_material_inexistente_eh_rejeitado(client, manager_token):
    response = client.post(
        "/itens",
        json={"name": "Tampa 500ml", "label": "tampa_500", "material_id": "00000000-0000-0000-0000-000000000000"},
        headers=auth_headers(manager_token),
    )

    assert response.status_code == 404


def test_cria_item_com_material_existente(client, manager_token):
    material = client.post("/materials", json={"code": "PEAD", "name": "Polietileno de alta densidade", "density": 0.95}, headers=auth_headers(manager_token))
    material_id = material.json()["id"]

    response = client.post("/itens", json={"name": "Tampa 500ml", "label": "tampa_500", "material_id": material_id}, headers=auth_headers(manager_token))

    assert response.status_code == 201
    assert response.json()["material_id"] == material_id


def test_edita_item(client, manager_token):
    created = client.post("/itens", json={"name": "Tampa 500ml", "label": "tampa_500"}, headers=auth_headers(manager_token))
    item_id = created.json()["id"]

    response = client.put(f"/itens/{item_id}", json={"name": "Tampa 500ml azul", "label": "tampa_500"}, headers=auth_headers(manager_token))

    assert response.status_code == 200
    assert response.json()["name"] == "Tampa 500ml azul"


def test_busca_item_por_label(client, manager_token):
    client.post("/itens", json={"name": "Tampa 500ml", "label": "tampa_500"}, headers=auth_headers(manager_token))

    response = client.get("/itens?q=tampa_500", headers=auth_headers(manager_token))

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_muda_status_do_item(client, manager_token):
    created = client.post("/itens", json={"name": "Tampa 500ml", "label": "tampa_500"}, headers=auth_headers(manager_token))
    item_id = created.json()["id"]

    response = client.patch(f"/itens/{item_id}/status?new_status=disable", headers=auth_headers(manager_token))

    assert response.status_code == 200
    assert response.json()["status"] == "disable"
