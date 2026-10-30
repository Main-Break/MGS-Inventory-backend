"""CRUD de itens: criar, editar, status (soft delete), label duplicado e material inexistente."""

from core import itens as data_itens
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


def test_import_row_cria_item_novo_quando_sku_nao_existe(client):
    success, item = data_itens.import_row({"name": "Importado", "label": "importado_novo", "sku": "SKU-IMPORT-1", "stock_quantity": 5})

    assert success
    assert item["sku"] == "SKU-IMPORT-1"


def test_import_row_atualiza_pelo_sku_quando_ja_existe(client):
    data_itens.import_row({"name": "Original", "label": "importado_original", "sku": "SKU-IMPORT-2", "stock_quantity": 5})

    success, atualizado = data_itens.import_row({"name": "Atualizado", "label": "importado_original", "sku": "SKU-IMPORT-2", "stock_quantity": 9})

    assert success
    assert atualizado["name"] == "Atualizado"
    assert atualizado["stock_quantity"] == 9

    # Continua sendo um item só, não duplicou.
    _, todos = data_itens.search("importado_original")
    assert len(todos) == 1


def test_import_row_sem_sku_sempre_cria_item_novo(client):
    data_itens.import_row({"name": "Sem SKU 1", "label": "sem_sku_1", "stock_quantity": 1})
    success, item = data_itens.import_row({"name": "Sem SKU 2", "label": "sem_sku_2", "stock_quantity": 1})

    assert success
    assert item["name"] == "Sem SKU 2"


def test_find_by_sku_nao_encontrado(client):
    success, result = data_itens.find_by_sku("NAO-EXISTE")

    assert not success
    assert result == "Item não encontrado."
