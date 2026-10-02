"""Funções base do sistema, fora da API. Roda direto:

    python cli.py
"""

from pathlib import Path

from pydantic import ValidationError

import core
from models.core import Core
from models.item import Item
from models.user import EmailJaCadastradoError, User
from schemas import UsuarioCriar
from security import criar_gestor_inicial, gerar_hash_senha


def _confirmar(pergunta: str) -> bool:
    return input(f"{pergunta} (s/n): ").strip().lower() in ("s", "sim")


def _criar_usuario() -> None:
    nome = input("nome: ").strip()
    email = input("e-mail: ").strip().lower()
    senha = input("senha (mínimo 8 caracteres): ").strip()
    role = "gestor" if _confirmar("é gestor?") else "funcionario"

    try:
        dados = UsuarioCriar(name=nome, email=email, password=senha, role=role)
    except ValidationError as erro:
        print("dados inválidos:", erro)
        return

    try:
        usuario = User(core.DB_FILE).criar(dados.name, dados.email, gerar_hash_senha(dados.password), dados.role)
    except EmailJaCadastradoError:
        print(f"já existe um usuário com o e-mail '{dados.email}'.")
        return
    print(f"usuário criado: id {usuario['id']}, {dados.role}.")


def _conferir_tabelas() -> None:
    Core(core.DB_FILE).migrate()
    print("tabelas conferidas/criadas em", core.DB_FILE)


def _conferir_gestor() -> None:
    criar_gestor_inicial()
    print("gestor inicial conferido/criado.")


def _itens_cadastrados() -> list[dict]:
    return Item(core.DB_FILE).buscar()


def _verificar_treinamento() -> None:
    modelo_existe = Path(core.MODEL_PATH).is_file()
    print(f"modelo em produção ({core.MODEL_PATH}): {'existe' if modelo_existe else 'não existe'}")

    datasets = sorted(core.TRAIN_DIR.glob("*.yaml")) if core.TRAIN_DIR.is_dir() else []
    if datasets:
        print(f"datasets encontrados em {core.TRAIN_DIR}:")
        for dataset in datasets:
            print(f"  - {dataset.name}")
    else:
        print(f"nenhum dataset .yaml encontrado em {core.TRAIN_DIR}")

    itens = _itens_cadastrados()
    print(f"itens cadastrados no catálogo: {len(itens)}")
    for item in itens:
        print(f"  - {item['label']} ({item['name']})")


def _treinar_modelo() -> None:
    itens = _itens_cadastrados()
    if not itens:
        print("nenhum item cadastrado no catálogo ainda. cadastre os itens antes de treinar.")
        return

    print("itens cadastrados (o label precisa bater com as classes do dataset):")
    for item in itens:
        print(f"  - {item['label']} ({item['name']})")

    caminho = input(f"\ncaminho do dataset.yaml (ex: {core.TRAIN_DIR}/dataset.yaml): ").strip()
    if not caminho:
        print("cancelado.")
        return

    if not _confirmar(f"confirma o treino com '{caminho}'?"):
        print("cancelado.")
        return

    from neural.treino import treinar

    treinar(caminho)


_OPCOES = {
    "1": ("Criar usuário", _criar_usuario),
    "2": ("Conferir/criar gestor inicial", _conferir_gestor),
    "3": ("Conferir/criar tabelas do banco", _conferir_tabelas),
    "4": ("Verificar treinamento (modelo, dataset, itens)", _verificar_treinamento),
    "5": ("Treinar modelo", _treinar_modelo),
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
