"""Fila de divergências: itens cujo peso teórico diverge do saldo do ERP."""

from core import itens
from tests.conftest import auth_headers


def criar_item(client, token, **campos):
    dados = {"name": "Item Teste", "label": "item_teste", "stock_quantity": 0, **campos}
    response = client.post("/itens", json=dados, headers=auth_headers(token))
    assert response.status_code == 201
    return response.json()


def test_item_sem_peso_ou_sem_saldo_erp_nao_aparece_na_divergencia(client, manager_token):
    criar_item(client, manager_token, label="sem_peso", stock_quantity=10)

    _, divergentes = itens.list_with_divergence()
    assert divergentes == []


def test_item_dentro_da_tolerancia_nao_aparece(client, manager_token):
    # 10 peças x 1kg = 10kg teórico; ERP com 10.2kg é só 2% de diferença, abaixo dos 5%.
    criar_item(client, manager_token, label="dentro_tolerancia", stock_quantity=10, weight_kg=1.0, stock_kg_erp=10.2)

    _, divergentes = itens.list_with_divergence()
    assert divergentes == []


def test_item_acima_da_tolerancia_aparece_com_os_campos_calculados(client, manager_token):
    # 10 peças x 1kg = 10kg teórico; ERP com 20kg é 100% de diferença.
    criar_item(client, manager_token, label="acima_tolerancia", stock_quantity=10, weight_kg=1.0, stock_kg_erp=20.0)

    _, divergentes = itens.list_with_divergence()

    assert len(divergentes) == 1
    item = divergentes[0]
    assert item["peso_teorico_kg"] == 10.0
    assert item["divergencia_kg"] == 10.0
    assert item["divergencia_pct"] == 50.0


def test_divergencias_ordenadas_pelo_maior_impacto_em_kg_primeiro(client, manager_token):
    criar_item(client, manager_token, label="divergencia_pequena", stock_quantity=10, weight_kg=1.0, stock_kg_erp=15.0)
    criar_item(client, manager_token, label="divergencia_grande", stock_quantity=10, weight_kg=1.0, stock_kg_erp=50.0)

    _, divergentes = itens.list_with_divergence()

    assert [item["label"] for item in divergentes] == ["divergencia_grande", "divergencia_pequena"]


def test_item_desativado_nao_entra_na_fila(client, manager_token):
    item = criar_item(client, manager_token, label="desativado", stock_quantity=10, weight_kg=1.0, stock_kg_erp=20.0)
    client.patch(f"/itens/{item['id']}/status?new_status=disable", headers=auth_headers(manager_token))

    _, divergentes = itens.list_with_divergence()
    assert divergentes == []
