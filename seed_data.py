"""
Preenche o banco com dados de exemplo, só para ver a interface com conteúdo.

    python seed_data.py

Não é parte do sistema (não é importado por nenhum outro arquivo), é uma
ferramenta de desenvolvimento. Pode ser rodado mais de uma vez: o que já
existe (material pela sigla, item pela label, usuário pelo e-mail) é
simplesmente ignorado, nada duplica.

As fotos das verificações de exemplo são só um nome de arquivo, o arquivo
de verdade não existe em data/upload/ (o link "ver foto" na interface
web vai dar 404). O que importa aqui é ver as telas com dado de verdade,
não simular o upload em si.
"""

import json
import random

from core import create_initial_manager, itens, materials, permissions, users, verifications
from util.security import hash_password

SENHA_PADRAO = "senha12345"

MATERIALS = [
    {"code": "PEAD", "name": "Polietileno de alta densidade", "density": 0.95, "description": "Usado em tampas e embalagens rígidas."},
    {"code": "PP", "name": "Polipropileno", "density": 0.90, "description": "Resistente à fadiga, usado em dobradiças."},
    {"code": "POM", "name": "Poliacetal", "density": 1.41, "description": "Alta rigidez e baixo atrito, usado em engrenagens."},
    {"code": "NYLON", "name": "Poliamida", "density": 1.14, "description": "Boa resistência mecânica e térmica."},
    {"code": "ABS", "name": "Acrilonitrila Butadieno Estireno", "density": 1.05, "description": "Usado em carcaças e peças injetadas."},
]

ITEMS = [
    {"name": "Tampa Rosca 28mm", "label": "tampa_rosca_28", "sku": "TR-28", "barcode": "7891234560012", "brand": "Plastline", "category": "Tampas", "material_code": "PEAD", "unit": "un", "weight_kg": 0.012, "stock_quantity": 4200, "min_stock": 500, "location": "Galpão A - Prateleira 3"},
    {"name": "Dobradiça Reforçada", "label": "dobradica_reforcada", "sku": "DB-01", "barcode": "7891234560029", "brand": "Flexmold", "category": "Dobradiças", "material_code": "PP", "unit": "un", "weight_kg": 0.034, "stock_quantity": 1800, "min_stock": 300, "location": "Galpão B - Prateleira 1"},
    {"name": "Engrenagem Z12", "label": "engrenagem_z12", "sku": "EG-12", "barcode": "7891234560036", "brand": "Precimold", "category": "Engrenagens", "material_code": "POM", "unit": "un", "weight_kg": 0.021, "stock_quantity": 950, "min_stock": 200, "location": "Galpão A - Prateleira 5"},
    {"name": "Suporte Nylon 6.6", "label": "suporte_nylon66", "sku": "SN-66", "barcode": "7891234560043", "brand": "Durapol", "category": "Suportes", "material_code": "NYLON", "unit": "un", "weight_kg": 0.045, "stock_quantity": 640, "min_stock": 150, "location": "Galpão C - Prateleira 2"},
    {"name": "Carcaça ABS Pequena", "label": "carcaca_abs_p", "sku": "CA-01", "barcode": "7891234560050", "brand": "Injetaplas", "category": "Carcaças", "material_code": "ABS", "unit": "un", "weight_kg": 0.088, "stock_quantity": 310, "min_stock": 100, "location": "Galpão C - Prateleira 4"},
    {"name": "Bucha de Fixação", "label": "bucha_fixacao", "sku": "BF-04", "barcode": "7891234560067", "brand": "Precimold", "category": "Buchas", "material_code": "POM", "unit": "un", "weight_kg": 0.008, "stock_quantity": 15, "min_stock": 500, "location": "Galpão A - Prateleira 6"},
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

        _, found = itens.search(data["label"])
        if any(item["label"] == data["label"] for item in found):
            continue

        exists, material = materials.find_by_code(material_code)
        data["material_id"] = material["id"] if exists else None

        itens.create(data)
        print(f"  item {data['label']} criado")


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
