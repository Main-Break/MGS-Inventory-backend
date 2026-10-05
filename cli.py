"""Funções base do sistema, fora da API. Roda direto:

    python cli.py
"""

from pathlib import Path

from pydantic import ValidationError

import config
from models.item import Item
from models.schema import Schema
from models.user import EmailAlreadyRegisteredError, User
from schemas import UserCreate
from security import create_initial_manager, hash_password


def _confirm(pergunta: str) -> bool:
    return input(f"{pergunta} (s/n): ").strip().lower() in ("s", "sim")


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

    try:
        user = User(config.DB_FILE).create(dados.name, dados.email, hash_password(dados.password), dados.role)
    except EmailAlreadyRegisteredError:
        print(f"já existe um usuário com o e-mail '{dados.email}'.")
        return
    print(f"usuário criado: id {user['id']}, {dados.role}.")


def _check_tables() -> None:
    Schema(config.DB_FILE).migrate()
    print("tabelas conferidas/criadas em", config.DB_FILE)


def _check_manager() -> None:
    create_initial_manager()
    print("gestor inicial conferido/criado.")


def _registered_items() -> list[dict]:
    return Item(config.DB_FILE).search()


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


_OPCOES = {
    "1": ("Criar usuário", _create_user),
    "2": ("Conferir/criar gestor inicial", _check_manager),
    "3": ("Conferir/criar tabelas do banco", _check_tables),
    "4": ("Verificar treinamento (modelo, dataset, itens)", _check_training),
    "5": ("Treinar modelo", _train_model),
}


def main() -> None:
    while True:
        print("\n--- CLI - Inventário por Foto ---")
        for chave, (descricao, _funcao) in _OPCOES.items():
            print(f"{chave}) {descricao}")
        print("0) Sair")

        escolha = input("> ").strip()
        if escolha == "0":
            break
        if escolha in _OPCOES:
            _OPCOES[escolha][1]()
        else:
            print("opção inválida.")


if __name__ == "__main__":
    main()
