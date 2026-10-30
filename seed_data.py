"""
Preenche o banco com dados de exemplo reais da MGS Plásticos de Engenharia, só para
ver a interface com conteúdo de verdade.

    python seed_data.py

Não é parte do sistema (não é importado por nenhum outro arquivo), é uma ferramenta
de desenvolvimento. Pode ser rodado mais de uma vez: o que já existe (material pela
sigla, item pela label, usuário pelo e-mail) é simplesmente ignorado, nada duplica.

Fontes dos dados: ~/Downloads/Tabela pesos e medidas 2021.pdf (densidades oficiais da
MGS) e ~/Downloads/lista de produtos mgs 2026.xls (nomes e dimensões reais dos
bastões e chapas do catálogo). Os pesos unitários dos itens são calculados aqui com
a mesma função usada pelo botão "Calcular peso" da interface (util/calculo_peso.py),
não digitados à mão.

As fotos das verificações de exemplo são só um nome de arquivo, o arquivo de verdade
não existe em data/upload/ (o link "ver foto" na interface web vai dar 404). O que
importa aqui é ver as telas com dado de verdade, não simular o upload em si.
"""

import json
import random

from core import create_initial_manager, itens, materials, permissions, users, verifications
from util.calculo_peso import peso_kg
from util.security import hash_password

SENHA_PADRAO = "senha12345"

# As 5 primeiras são a tabela oficial da MGS. As demais são valores de referência de
# mercado (a MGS também trabalha com esses materiais, conforme o catálogo de
# produtos, mas a densidade deles não está na tabela oficial de pesos e medidas).
MATERIALS = [
    {"code": "NY6", "name": "Poliamida 6 (Nylon 6)", "density": 1.14, "description": "Tabela de pesos e medidas MGS 2021."},
    {"code": "NY66", "name": "Poliamida 6.6 (Nylon 6.6)", "density": 1.14, "description": "Tabela de pesos e medidas MGS 2021."},
    {"code": "PP", "name": "Polipropileno", "density": 0.91, "description": "Tabela de pesos e medidas MGS 2021."},
    {"code": "PEAD", "name": "Polietileno de alta densidade", "density": 0.95, "description": "Tabela de pesos e medidas MGS 2021."},
    {"code": "POM", "name": "Poliacetal", "density": 1.41, "description": "Tabela de pesos e medidas MGS 2021."},
    {"code": "PTFE", "name": "Politetrafluoretileno (Teflon)", "density": 2.20, "description": "Densidade de referência de mercado, não consta na tabela oficial MGS."},
    {"code": "PVDF", "name": "Fluoreto de polivinilideno", "density": 1.78, "description": "Densidade de referência de mercado, não consta na tabela oficial MGS."},
    {"code": "UHMW", "name": "Polietileno de ultra alto peso molecular", "density": 0.94, "description": "Densidade de referência de mercado, não consta na tabela oficial MGS."},
    {"code": "CELERON", "name": "Fenólico (Celeron)", "density": 1.35, "description": "Densidade de referência de mercado, não consta na tabela oficial MGS."},
]

# name/label/sku/shape e as dimensões em cm vêm do catálogo real (lista de produtos
# mgs 2026.xls). peças_estoque e kg_erp simulam o relatório do ERP: a maioria bate
# com o peso teórico, alguns ficam propositalmente divergentes (mesmo cenário do
# piloto descrito na proposta de parceria: peças registradas não bate com o kg).
ITEMS = [
    {"name": "Bastão 100x3000mm POM", "label": "bastao_100x3000_pom", "sku": "MGS-1188", "material_code": "POM",
     "shape": "bastao_redondo", "width_cm": 10, "length_cm": 300, "stock_quantity": 40, "divergente": False},
    {"name": "Bastão 100x1000mm Ny6", "label": "bastao_100x1000_ny6", "sku": "CFE-48", "material_code": "NY6",
     "shape": "bastao_redondo", "width_cm": 10, "length_cm": 100, "stock_quantity": 12, "divergente": False},
    {"name": "Bastão 60x1000mm Ny6 AZ", "label": "bastao_60x1000_ny6_az", "sku": "MGS-38", "material_code": "NY6",
     "shape": "bastao_redondo", "width_cm": 6, "length_cm": 100, "stock_quantity": 72, "divergente": False},
    {"name": "Bastão 32x1000mm Ny6", "label": "bastao_32x1000_ny6", "sku": "MGS-26", "material_code": "NY6",
     "shape": "bastao_redondo", "width_cm": 3.2, "length_cm": 100, "stock_quantity": 434, "divergente": False},
    {"name": "Bastão 20x3000mm PVDF", "label": "bastao_20x3000_pvdf", "sku": "FL-1173", "material_code": "PVDF",
     "shape": "bastao_redondo", "width_cm": 2, "length_cm": 300, "stock_quantity": 25, "divergente": False},
    {"name": "Bastão 65x1000mm PTFE", "label": "bastao_65x1000_ptfe", "sku": "FL-11799", "material_code": "PTFE",
     "shape": "bastao_redondo", "width_cm": 6.5, "length_cm": 100, "stock_quantity": 18, "divergente": False},
    {"name": "Chapa 10x1000x2000mm Ny6", "label": "chapa_10x1000x2000_ny6", "sku": "1000210", "material_code": "NY6",
     "shape": "chapa", "height_cm": 1, "width_cm": 100, "length_cm": 200, "stock_quantity": 8, "divergente": False},
    {"name": "Chapa 50x1220x3050mm UHMW", "label": "chapa_50x1220x3050_uhmw", "sku": "1000123", "material_code": "UHMW",
     "shape": "chapa", "height_cm": 5, "width_cm": 122, "length_cm": 305, "stock_quantity": 6, "divergente": False},
    {"name": "Chapa 25x1000x1000mm Celeron", "label": "chapa_25x1000x1000_celeron", "sku": "FGM-252927", "material_code": "CELERON",
     "shape": "chapa", "height_cm": 2.5, "width_cm": 100, "length_cm": 100, "stock_quantity": 83, "divergente": True},
    {"name": "Bastão 150x3000mm Ny6", "label": "bastao_150x3000_ny6", "sku": "MGS-6813", "material_code": "NY6",
     "shape": "bastao_redondo", "width_cm": 15, "length_cm": 300, "stock_quantity": 0, "divergente": True},
]

EMPLOYEES = [
    {"name": "Carla Mendes", "email": "carla.mendes@teste.com", "permissions": ["itens.create", "itens.edit"]},
    {"name": "Bruno Alves", "email": "bruno.alves@teste.com", "permissions": ["materials.create", "materials.edit"]},
    {"name": "Fernanda Lima", "email": "fernanda.lima@teste.com", "permissions": ["verifications.view_all", "verifications.approve"]},
    {"name": "Diego Souza", "email": "diego.souza@teste.com", "permissions": []},
]


def seed_materials() -> None:
    for data in MATERIALS:
        exists, _ = materials.find_by_code(data["code"])
        if exists:
            continue
        materials.create(data)
        print(f"  material {data['code']} criado")


def seed_itens() -> None:
    for original in ITEMS:
        data = dict(original)
        material_code = data.pop("material_code")
        divergente = data.pop("divergente")

        _, found = itens.search(data["label"])
        if any(item["label"] == data["label"] for item in found):
            continue

        exists, material = materials.find_by_code(material_code)
        data["material_id"] = material["id"] if exists else None

        # Peso unitário calculado pela mesma fórmula do botão "Calcular peso" da interface.
        weight = peso_kg(data["shape"], float(material["density"]), data.get("height_cm", 0), data.get("width_cm", 0), data.get("length_cm", 0))
        data["weight_kg"] = weight

        peso_teorico = weight * data["stock_quantity"]
        if divergente:
            # Replica o caso real da proposta de parceria: kg registrado no ERP sem
            # as peças correspondentes (ex: item MGS-83, 83kg em estoque, 0 peças
            # registradas). Quando o peso teórico já é zero (0 peças), usa um saldo
            # de ERP fixo, senão a divergência simulada também seria zero.
            data["stock_kg_erp"] = round(peso_teorico * 2.6, 3) if peso_teorico else round(weight * 50, 3)
        else:
            data["stock_kg_erp"] = round(peso_teorico, 3)
        data["min_stock"] = 10
        data["location"] = "Galpão A - Cantoneira 12"

        itens.create(data)
        print(f"  item {data['label']} criado (peso unitário calculado: {weight} kg)")


def seed_employees() -> list[dict]:
    created = []
    for employee in EMPLOYEES:
        exists, user = users.find_by_email(employee["email"])
        if not exists:
            _, user = users.create(employee["name"], employee["email"], hash_password(SENHA_PADRAO), "funcionario")
            print(f"  funcionário {employee['email']} criado (senha: {SENHA_PADRAO})")

        for permission in employee["permissions"]:
            permissions.grant(user["id"], permission)

        created.append(user)
    return created


def seed_verifications(employees: list[dict]) -> None:
    _, existing = verifications.list_all()
    if existing or not employees:
        return

    _, all_itens = itens.list_all()
    if not all_itens:
        return

    # Algumas aprovadas, uma reprovada, outras pendentes, pra ver os três estados na listagem.
    status_por_amostra = [True, False, None, True, None]

    for index, approved in enumerate(status_por_amostra):
        item = all_itens[index % len(all_itens)]
        employee = employees[index % len(employees)]

        detection = {"label": item["label"], "count": random.randint(5, 80), "confidence": round(random.uniform(0.82, 0.98), 2)}
        _, created = verifications.create(employee["id"], item["id"], f"exemplo-{item['label']}.jpg", json.dumps([detection]))

        if approved is not None:
            verifications.approve(created["id"], approved)

    print("  verificações de exemplo criadas")


def main() -> None:
    create_initial_manager()
    print("Gestor inicial garantido (ADMIN_EMAIL/ADMIN_PASSWORD do .env).")

    print("Materiais:")
    seed_materials()

    print("Itens:")
    seed_itens()

    print("Funcionários:")
    employees = seed_employees()

    print("Verificações:")
    seed_verifications(employees)

    print(f"\nPronto. Funcionários de exemplo usam a senha '{SENHA_PADRAO}'.")


if __name__ == "__main__":
    main()
