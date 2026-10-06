"""Funções base do sistema, fora da API. Roda direto:

    python cli.py

Isso roda no servidor, direto no banco, sem passar pela autenticação da
API. Quem tem acesso ao terminal já tem acesso total: criar/editar/apagar
qualquer usuário, trocar função, aprovar verificação, etc.
"""

import json
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable

from pydantic import ValidationError

import config
from models.item import DataItem
from models.schema import DataSchema
from models.user import DataUser
from models.verification import DataVerification
from schemas import UserCreate
from security import create_initial_manager, hash_password

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


def _read_id(mensagem: str) -> int | None:
    bruto = input(mensagem).strip()

    if not bruto.isdigit():
        print("id inválido.")
        return None
    return int(bruto)


# --- usuários --------------------------------------------------------------


def _users() -> DataUser:
    return DataUser(config.DB_FILE)


def _user_row(user: dict) -> tuple:
    return (user["id"], user["name"], user["email"], user["role"], "sim" if user["active"] else "não")


_USER_HEADERS = ["id", "nome", "e-mail", "função", "ativo"]


def _find_user_or_warn(user_id: int) -> dict | None:
    sucesso, resultado = _users().find_by_id(user_id)

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

    sucesso, resultado = _users().create(dados.name, dados.email, hash_password(dados.password), dados.role)

    if not sucesso:
        print(resultado)
        return

    print(f"usuário criado: id {resultado['id']}, {dados.role}.")


def _search_users() -> None:
    termo = input("buscar por nome/e-mail (enter pra listar todos): ").strip()
    _, resultados = _users().search(termo or None)

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

    _, atualizado = _users().update(user["id"], nome, email, user["password_hash"])
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

    _users().update(user["id"], user["name"], user["email"], hash_password(senha))
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

    _users().set_role(user["id"], nova_role)
    print(f"função atualizada para '{nova_role}'.")


def _toggle_user_active() -> None:
    user_id = _read_id("id do usuário: ")
    if user_id is None:
        return

    user = _find_user_or_warn(user_id)
    if user is None:
        return

    ativo_atual = bool(user["active"])
    acao = "desativar" if ativo_atual else "ativar"
    if not _confirm(f"{acao} '{user['email']}'?"):
        print("cancelado.")
        return

    _users().set_active(user["id"], not ativo_atual)
    print(f"usuário {'desativado' if ativo_atual else 'ativado'}.")


_MENU_USUARIOS: dict[str, tuple[str, Callable[[], None]]] = {
    "1": ("Criar usuário", _create_user),
    "2": ("Buscar/listar usuários", _search_users),
    "3": ("Editar nome/e-mail", _edit_user_profile),
    "4": ("Trocar senha", _change_user_password),
    "5": ("Trocar função (gestor/funcionário)", _change_user_role),
    "6": ("Ativar/desativar", _toggle_user_active),
}


# --- itens do catálogo -------------------------------------------------


def _items() -> DataItem:
    return DataItem(config.DB_FILE)


def _registered_items() -> list[dict]:
    _, resultado = _items().search()
    return resultado


def _item_row(item: dict) -> tuple:
    return (item["id"], item["label"], item["name"], item["stock_quantity"])


_ITEM_HEADERS = ["id", "label", "nome", "estoque"]


def _create_item() -> None:
    label = input("label (nome exato da classe que o modelo de IA devolve): ").strip()
    nome = input("nome: ").strip()
    estoque_bruto = input("estoque inicial (enter = 0): ").strip()
    estoque = int(estoque_bruto) if estoque_bruto.isdigit() else 0

    sucesso, resultado = _items().create(label, nome, estoque)

    if not sucesso:
        print(resultado)
        return

    print(f"item criado: id {resultado['id']}.")


def _search_items() -> None:
    termo = input("buscar por nome/label (enter pra listar todos): ").strip()
    _, resultados = _items().search(termo or None)

    _show_paginated(_ITEM_HEADERS, [_item_row(item) for item in resultados])


_MENU_ITENS: dict[str, tuple[str, Callable[[], None]]] = {
    "1": ("Criar item", _create_item),
    "2": ("Buscar/listar itens", _search_items),
}


# --- verificações --------------------------------------------------------


def _verifications() -> DataVerification:
    return DataVerification(config.DB_FILE)


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

    if filtro_usuario.isdigit():
        _, resultados = _verifications().list_by_user(int(filtro_usuario))
    else:
        _, resultados = _verifications().list_all()

    _show_paginated(_VERIFICATION_HEADERS, [_verification_row(linha) for linha in resultados])


def _approve_verification() -> None:
    verification_id = _read_id("id da verificação: ")
    if verification_id is None:
        return

    sucesso, linha = _verifications().find_by_id(verification_id)
    if not sucesso:
        print(linha)
        return

    print(f"status atual: {_aprovado_texto(linha['approved'])}")
    aprovar = _confirm("aprovar")

    _verifications().approve(verification_id, aprovar)
    print(f"verificação marcada como {_aprovado_texto(aprovar)}.")


_MENU_VERIFICACOES: dict[str, tuple[str, Callable[[], None]]] = {
    "1": ("Listar verificações", _list_verifications),
    "2": ("Aprovar/reprovar verificação", _approve_verification),
}


# --- banco de dados / sistema --------------------------------------------


def _check_tables() -> None:
    DataSchema(config.DB_FILE).migrate()
    print("tabelas conferidas/criadas em", config.DB_FILE)


def _check_manager() -> None:
    create_initial_manager()
    print("gestor inicial conferido/criado.")


def _check_training() -> None:
    modelo_existe = Path(config.MODEL_PATH).is_file()
    print(f"modelo em produção ({config.MODEL_PATH}): {'existe' if modelo_existe else 'não existe'}")

    datasets = sorted(config.TRAIN_DIR.glob("*.yaml")) if config.TRAIN_DIR.is_dir() else []
    if datasets:
        print(f"datasets encontrados em {config.TRAIN_DIR}:")
        for dataset in datasets:
            print(f"  - {dataset.name}")
    else:
        print(f"nenhum dataset .yaml encontrado em {config.TRAIN_DIR}")

    itens = _registered_items()
    print(f"itens cadastrados no catálogo: {len(itens)}")
    for item in itens:
        print(f"  - {item['label']} ({item['name']})")


def _train_model() -> None:
    itens = _registered_items()
    if not itens:
        print("nenhum item cadastrado no catálogo ainda. cadastre os itens antes de treinar.")
        return

    print("itens cadastrados (o label precisa bater com as classes do dataset):")
    for item in itens:
        print(f"  - {item['label']} ({item['name']})")

    caminho = input(f"\ncaminho do dataset.yaml (ex: {config.TRAIN_DIR}/dataset.yaml): ").strip()
    if not caminho:
        print("cancelado.")
        return

    if not _confirm(f"confirma o treino com '{caminho}'?"):
        print("cancelado.")
        return

    from neural.treino import train

    train(caminho)


def _backup_database() -> None:
    """Cópia a quente do SQLite (sqlite3 Connection.backup), segura mesmo
    com o servidor rodando e escrevendo no banco ao mesmo tempo."""
    origem = Path(config.DB_FILE)
    if not origem.is_file():
        print(f"banco não encontrado em '{origem}'.")
        return

    pasta_backups = config.BASE_DIR / "backups"
    pasta_backups.mkdir(parents=True, exist_ok=True)

    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = pasta_backups / f"{origem.stem}_{carimbo}.db"

    with sqlite3.connect(origem) as conexao_origem, sqlite3.connect(destino) as conexao_destino:
        conexao_origem.backup(conexao_destino)

    print(f"backup criado em: {destino}")


def _run_tests() -> None:
    print("rodando a suíte de testes (pytest)...\n")
    resultado = subprocess.run([sys.executable, "-m", "pytest"])

    print("\ntodos os testes passaram." if resultado.returncode == 0 else "\nalguns testes falharam, veja acima.")


_MENU_SISTEMA: dict[str, tuple[str, Callable[[], None]]] = {
    "1": ("Conferir/criar gestor inicial", _check_manager),
    "2": ("Conferir/criar tabelas do banco", _check_tables),
    "3": ("Verificar treinamento (modelo, dataset, itens)", _check_training),
    "4": ("Treinar modelo", _train_model),
    "5": ("Criar backup do banco", _backup_database),
    "6": ("Rodar testes (pytest)", _run_tests),
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
    "2": ("Itens do catálogo", lambda: _run_menu("Itens do catálogo", _MENU_ITENS)),
    "3": ("Verificações", lambda: _run_menu("Verificações", _MENU_VERIFICACOES)),
    "4": ("Banco de dados / sistema", lambda: _run_menu("Banco de dados / sistema", _MENU_SISTEMA)),
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
