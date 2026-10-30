"""Funções administrativas do sistema, fora da API. Para rodar, na raiz do projeto:

    python -m CLI.cli

Isso roda no servidor, direto no banco, sem passar pela autenticação da
API. Quem tem acesso ao terminal já tem acesso total: criar/editar/apagar
qualquer usuário, trocar função, aprovar verificação, etc.
"""

import json
import uuid
from typing import Callable

from pydantic import ValidationError

from core import config, create_initial_manager, itens, materials, neural, permissions, user_permissions, users, verifications
from models.permissions import DataPermission
from models.schemas import ItemData, MaterialData, UserCreate
from neural.train import Train
from util.security import hash_password

_PAGE_SIZE = 10


# --- exibição: tabela e paginação ---------------------------------------


def _print_table(headers: list[str], rows: list[tuple]) -> None:
    if not rows:
        print("nenhum resultado.")
        return

    larguras = [len(cabecalho) for cabecalho in headers]
    for linha in rows:
        for indice, valor in enumerate(linha):
            larguras[indice] = max(larguras[indice], len(str(valor)))

    def _formata(linha) -> str:
        return "  ".join(str(valor).ljust(larguras[indice]) for indice, valor in enumerate(linha))

    print(_formata(headers))
    print("  ".join("-" * largura for largura in larguras))
    for linha in rows:
        print(_formata(linha))


def _show_paginated(headers: list[str], rows: list[tuple]) -> None:
    if not rows:
        print("nenhum resultado.")
        return

    total = len(rows)
    inicio = 0

    while True:
        pagina = rows[inicio : inicio + _PAGE_SIZE]
        _print_table(headers, pagina)

        fim = min(inicio + _PAGE_SIZE, total)
        print(f"\n-- {fim}/{total} --")

        if fim >= total:
            return
        if input("[enter] próxima página, [q] parar: ").strip().lower() == "q":
            return

        inicio = fim


# --- genéricos -----------------------------------------------------------


def _confirm(pergunta: str) -> bool:
    return input(f"{pergunta} (s/n): ").strip().lower() in ("s", "sim")


def _read_id(mensagem: str) -> str | None:
    """Os ids são UUID, ex: 3f1c9a2e-8b4d-4e6f-9a1b-2c3d4e5f6a7b."""
    bruto = input(mensagem).strip()

    try:
        return str(uuid.UUID(bruto))
    except ValueError:
        print("id inválido.")
        return None


def _ask_optional(pergunta: str) -> str | None:
    """Pergunta um campo opcional. Enter em branco vira None."""
    return input(pergunta).strip() or None


def _ask_number(pergunta: str, padrao=None):
    """Pergunta um número (aceita vírgula ou ponto). Enter em branco devolve o padrão."""
    bruto = input(pergunta).strip().replace(",", ".")
    if not bruto:
        return padrao

    try:
        return float(bruto)
    except ValueError:
        print("número inválido, campo ignorado.")
        return padrao


# --- usuários --------------------------------------------------------------


def _user_row(user: dict) -> tuple:
    return (user["id"], user["name"], user["email"], user["role"], user["status"])


_USER_HEADERS = ["id", "nome", "e-mail", "função", "status"]


def _find_user_or_warn(user_id: str) -> dict | None:
    sucesso, resultado = users.find_by_id(user_id)

    if not sucesso:
        print(resultado)
        return None
    return resultado


def _create_user() -> None:
    nome = input("nome: ").strip()
    email = input("e-mail: ").strip().lower()
    senha = input("senha (mínimo 8 caracteres): ").strip()
    role = "gestor" if _confirm("é gestor?") else "funcionario"

    try:
        dados = UserCreate(name=nome, email=email, password=senha, role=role)
    except ValidationError as erro:
        print("dados inválidos:", erro)
        return

    sucesso, resultado = users.create(dados.name, dados.email, hash_password(dados.password), dados.role)

    if not sucesso:
        print(resultado)
        return

    print(f"usuário criado: id {resultado['id']}, {dados.role}.")


def _search_users() -> None:
    termo = input("buscar por nome/e-mail (enter pra listar todos): ").strip()
    _, resultados = users.search(termo or None)

    _show_paginated(_USER_HEADERS, [_user_row(user) for user in resultados])


def _edit_user_profile() -> None:
    user_id = _read_id("id do usuário: ")
    if user_id is None:
        return

    user = _find_user_or_warn(user_id)
    if user is None:
        return

    print(f"atual: {user['name']} <{user['email']}>")
    nome = input(f"novo nome (enter mantém '{user['name']}'): ").strip() or user["name"]
    email = input(f"novo e-mail (enter mantém '{user['email']}'): ").strip().lower() or user["email"]

    _, atualizado = users.update(user["id"], nome, email, user["password_hash"])
    print(f"atualizado: {atualizado['name']} <{atualizado['email']}>")


def _change_user_password() -> None:
    user_id = _read_id("id do usuário: ")
    if user_id is None:
        return

    user = _find_user_or_warn(user_id)
    if user is None:
        return

    senha = input("nova senha (mínimo 8 caracteres): ").strip()
    if len(senha) < 8:
        print("senha curta demais, precisa de pelo menos 8 caracteres.")
        return

    if not _confirm(f"trocar a senha de '{user['email']}'?"):
        print("cancelado.")
        return

    users.update(user["id"], user["name"], user["email"], hash_password(senha))
    print("senha trocada.")


def _change_user_role() -> None:
    user_id = _read_id("id do usuário: ")
    if user_id is None:
        return

    user = _find_user_or_warn(user_id)
    if user is None:
        return

    nova_role = "funcionario" if user["role"] == "gestor" else "gestor"
    if not _confirm(f"trocar '{user['email']}' de '{user['role']}' para '{nova_role}'?"):
        print("cancelado.")
        return

    users.set_role(user["id"], nova_role)
    print(f"função atualizada para '{nova_role}'.")


def _change_user_status() -> None:
    user_id = _read_id("id do usuário: ")
    if user_id is None:
        return

    user = _find_user_or_warn(user_id)
    if user is None:
        return

    print(f"status atual: {user['status']}")
    novo_status = input("novo status (active, disable, deleted): ").strip()
    if novo_status not in ("active", "disable", "deleted"):
        print("status inválido.")
        return

    if not _confirm(f"mudar '{user['email']}' para '{novo_status}'?"):
        print("cancelado.")
        return

    users.set_status(user["id"], novo_status)
    print(f"status atualizado para '{novo_status}'.")


def _manage_permissions() -> None:
    user_id = _read_id("id do usuário: ")
    if user_id is None:
        return

    user = _find_user_or_warn(user_id)
    if user is None:
        return

    if user["role"] == "gestor":
        print("gestor já pode tudo, não precisa liberar permissões.")
        return

    chaves = list(DataPermission.PERMISSIONS)

    while True:
        liberadas = user_permissions(user)
        print(f"\npermissões de '{user['email']}' ([x] = liberada):")
        for numero, chave in enumerate(chaves, start=1):
            marca = "x" if chave in liberadas else " "
            print(f"  {numero:2}) [{marca}] {DataPermission.PERMISSIONS[chave]} ({chave})")

        escolha = input("número para liberar/retirar (enter = sair): ").strip()
        if not escolha:
            return
        if not escolha.isdigit() or not 1 <= int(escolha) <= len(chaves):
            print("opção inválida.")
            continue

        chave = chaves[int(escolha) - 1]
        if chave in liberadas:
            permissions.revoke(user["id"], chave)
            print(f"retirada: {chave}")
        else:
            permissions.grant(user["id"], chave)
            print(f"liberada: {chave}")


_MENU_USUARIOS: dict[str, tuple[str, Callable[[], None]]] = {
    "1": ("Criar usuário", _create_user),
    "2": ("Buscar/listar usuários", _search_users),
    "3": ("Editar nome/e-mail", _edit_user_profile),
    "4": ("Trocar senha", _change_user_password),
    "5": ("Trocar função (gestor/funcionário)", _change_user_role),
    "6": ("Mudar status (ativo, desativado, apagado)", _change_user_status),
    "7": ("Permissões (liberar/retirar)", _manage_permissions),
}


# --- materiais ------------------------------------------------------------


def _material_row(material: dict) -> tuple:
    return (material["id"], material["code"], material["name"], material["density"], material["status"])


_MATERIAL_HEADERS = ["id", "sigla", "nome", "densidade (g/cm³)", "status"]


def _create_material() -> None:
    print("campos com * são obrigatórios.")
    dados = {
        "code": input("* sigla (PEAD, PP, POM, NYLON...): ").strip(),
        "name": input("* nome completo: ").strip(),
        "density": _ask_number("* densidade / peso específico em g/cm³ (ex: 0,95): "),
        "description": _ask_optional("observações: "),
    }

    try:
        material = MaterialData(**dados)
    except ValidationError as erro:
        print("dados inválidos:", erro)
        return

    sucesso, resultado = materials.create(material.model_dump())

    if not sucesso:
        print(resultado)
        return

    print(f"material criado: {resultado['code']}, id {resultado['id']}.")


def _search_materials() -> None:
    termo = input("buscar por sigla ou nome (enter pra listar todos): ").strip()
    _, resultados = materials.search(termo or None)

    _show_paginated(_MATERIAL_HEADERS, [_material_row(material) for material in resultados])


def _ask_material() -> str | None | bool:
    """
    Pergunta a sigla do material do item e devolve o id dele.
    Enter em branco devolve None (item sem material). Sigla inexistente devolve False.
    """
    sigla = input("sigla do material (PEAD, PP, POM... enter = sem material): ").strip()
    if not sigla:
        return None

    sucesso, resultado = materials.find_by_code(sigla)
    if not sucesso:
        print(f"{resultado} cadastre o material antes, no menu Materiais.")
        return False
    return resultado["id"]


_MENU_MATERIAIS: dict[str, tuple[str, Callable[[], None]]] = {
    "1": ("Criar material", _create_material),
    "2": ("Buscar/listar materiais", _search_materials),
}


# --- itens do catálogo -------------------------------------------------


def _registered_items() -> list[dict]:
    _, resultado = itens.search()
    return resultado


def _item_row(item: dict) -> tuple:
    return (item["id"], item["label"], item["name"], item["sku"] or "-", item["stock_quantity"], item["status"])


_ITEM_HEADERS = ["id", "label", "nome", "sku", "estoque", "status"]


def _create_item() -> None:
    print("campos com * são obrigatórios, os outros podem ficar em branco (enter).")
    material_id = _ask_material()
    if material_id is False:
        return

    dados = {
        "material_id": material_id,
        "name": input("* nome: ").strip(),
        "label": input("* label (nome exato da classe que o modelo de IA devolve): ").strip(),
        "description": _ask_optional("descrição: "),
        "sku": _ask_optional("SKU: "),
        "barcode": _ask_optional("código de barras: "),
        "brand": _ask_optional("marca: "),
        "category": _ask_optional("categoria: "),
        "unit": _ask_optional("unidade (un, cx, pct, kg... enter = un): ") or "un",
        "weight_kg": _ask_number("peso em kg: "),
        "height_cm": _ask_number("altura em cm: "),
        "width_cm": _ask_number("largura em cm: "),
        "length_cm": _ask_number("comprimento em cm: "),
        "stock_quantity": int(_ask_number("estoque atual (enter = 0): ", 0)),
        "min_stock": int(_ask_number("estoque mínimo (enter = 0): ", 0)),
        "location": _ask_optional("local no estoque (galpão, prateleira...): "),
    }

    try:
        item = ItemData(**dados)
    except ValidationError as erro:
        print("dados inválidos:", erro)
        return

    sucesso, resultado = itens.create(item.model_dump())

    if not sucesso:
        print(resultado)
        return

    print(f"item criado: id {resultado['id']}.")


def _search_items() -> None:
    termo = input("buscar por nome, label, SKU ou código de barras (enter pra listar todos): ").strip()
    _, resultados = itens.search(termo or None)

    _show_paginated(_ITEM_HEADERS, [_item_row(item) for item in resultados])


_MENU_ITENS: dict[str, tuple[str, Callable[[], None]]] = {
    "1": ("Criar item", _create_item),
    "2": ("Buscar/listar itens", _search_items),
}


# --- verificações --------------------------------------------------------


def _aprovado_texto(aprovado) -> str:
    if aprovado is None:
        return "pendente"
    return "sim" if aprovado else "não"


def _verification_row(linha: dict) -> tuple:
    qtd_deteccoes = len(json.loads(linha["detections"]))
    return (
        linha["id"],
        linha["user_id"],
        linha["item_id"] if linha["item_id"] is not None else "-",
        qtd_deteccoes,
        _aprovado_texto(linha["approved"]),
        linha["created_at"],
    )


_VERIFICATION_HEADERS = ["id", "usuário", "item", "detecções", "aprovado", "criado em"]


def _list_verifications() -> None:
    filtro_usuario = input("filtrar por id de usuário (enter pra listar todas): ").strip()

    if filtro_usuario:
        _, resultados = verifications.list_by_user(filtro_usuario)
    else:
        _, resultados = verifications.list_all()

    _show_paginated(_VERIFICATION_HEADERS, [_verification_row(linha) for linha in resultados])


def _approve_verification() -> None:
    verification_id = _read_id("id da verificação: ")
    if verification_id is None:
        return

    sucesso, linha = verifications.find_by_id(verification_id)
    if not sucesso:
        print(linha)
        return

    print(f"status atual: {_aprovado_texto(linha['approved'])}")
    aprovar = _confirm("aprovar")

    verifications.approve(verification_id, aprovar)
    print(f"verificação marcada como {_aprovado_texto(aprovar)}.")


_MENU_VERIFICACOES: dict[str, tuple[str, Callable[[], None]]] = {
    "1": ("Listar verificações", _list_verifications),
    "2": ("Aprovar/reprovar verificação", _approve_verification),
}


# --- banco de dados / sistema --------------------------------------------


def _check_manager() -> None:
    create_initial_manager()
    print("gestor inicial conferido/criado.")


def _check_training() -> None:
    print(f"modelo em produção ({config.MODEL_PATH}): {'existe' if neural.is_available() else 'não existe'}")

    datasets = sorted(config.TRAIN_DIR.glob("*.yaml")) if config.TRAIN_DIR.is_dir() else []
    if datasets:
        print(f"datasets encontrados em {config.TRAIN_DIR}:")
        for dataset in datasets:
            print(f"  - {dataset.name}")
    else:
        print(f"nenhum dataset .yaml encontrado em {config.TRAIN_DIR}")

    cadastrados = _registered_items()
    print(f"itens cadastrados: {len(cadastrados)}")
    for item in cadastrados:
        print(f"  - {item['label']} ({item['name']})")


def _train_model() -> None:
    cadastrados = _registered_items()
    if not cadastrados:
        print("nenhum item cadastrado ainda. cadastre os itens antes de treinar.")
        return

    print("itens cadastrados (o label precisa bater com as classes do dataset):")
    for item in cadastrados:
        print(f"  - {item['label']} ({item['name']})")

    caminho = input(f"\ncaminho do dataset.yaml (ex: {config.TRAIN_DIR}/dataset.yaml): ").strip()
    if not caminho:
        print("cancelado.")
        return

    if not _confirm(f"confirma o treino com '{caminho}'?"):
        print("cancelado.")
        return

    Train(config.MODEL_PATH, config.TRAIN_DIR / "runs").run(caminho)


_MENU_SISTEMA: dict[str, tuple[str, Callable[[], None]]] = {
    "1": ("Conferir/criar gestor inicial", _check_manager),
    "2": ("Verificar treinamento (modelo, dataset, itens)", _check_training),
    "3": ("Treinar modelo", _train_model),
}


# --- menus -----------------------------------------------------------------


def _run_menu(titulo: str, opcoes: dict[str, tuple[str, Callable[[], None]]]) -> None:
    while True:
        print(f"\n--- {titulo} ---")
        for chave, (descricao, _) in opcoes.items():
            print(f"{chave}) {descricao}")
        print("0) Voltar")

        escolha = input("> ").strip()
        if escolha == "0":
            return

        if escolha in opcoes:
            opcoes[escolha][1]()
        else:
            print("opção inválida.")


_MENU_PRINCIPAL: dict[str, tuple[str, Callable[[], None]]] = {
    "1": ("Usuários", lambda: _run_menu("Usuários", _MENU_USUARIOS)),
    "2": ("Materiais", lambda: _run_menu("Materiais", _MENU_MATERIAIS)),
    "3": ("Itens", lambda: _run_menu("Itens", _MENU_ITENS)),
    "4": ("Verificações", lambda: _run_menu("Verificações", _MENU_VERIFICACOES)),
    "5": ("Banco de dados / sistema", lambda: _run_menu("Banco de dados / sistema", _MENU_SISTEMA)),
}


def main() -> None:
    while True:
        print("\n=== CLI - Inventário por Foto (acesso administrativo) ===")
        for chave, (descricao, _) in _MENU_PRINCIPAL.items():
            print(f"{chave}) {descricao}")
        print("0) Sair")

        escolha = input("> ").strip()
        if escolha == "0":
            break

        if escolha in _MENU_PRINCIPAL:
            _MENU_PRINCIPAL[escolha][1]()
        else:
            print("opção inválida.")


if __name__ == "__main__":
    main()
