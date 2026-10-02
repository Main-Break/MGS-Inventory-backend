"""Testa o model User direto no banco, sem passar pela API."""

import pytest

from models.core import Core
from models.user import EmailJaCadastradoError, User


@pytest.fixture
def usuarios(tmp_path) -> User:
    db_file = str(tmp_path / "teste.db")
    Core(db_file).migrate()
    return User(db_file)


def test_criar_e_buscar_por_email(usuarios: User):
    criado = usuarios.criar("Ana", "ana@exemplo.com", "hash-falso", "funcionario")

    assert criado["id"] is not None
    assert usuarios.buscar_por_email("ana@exemplo.com")["name"] == "Ana"


def test_nao_deixa_duplicar_email(usuarios: User):
    usuarios.criar("Ana", "ana@exemplo.com", "hash-falso")

    with pytest.raises(EmailJaCadastradoError):
        usuarios.criar("Outra Ana", "ana@exemplo.com", "outro-hash")


def test_mudar_acesso_usuario_inexistente_retorna_none(usuarios: User):
    assert usuarios.mudar_acesso(999, False) is None


def test_mudar_acesso_desativa_usuario(usuarios: User):
    criado = usuarios.criar("Ana", "ana@exemplo.com", "hash-falso")

    atualizado = usuarios.mudar_acesso(criado["id"], False)

    assert atualizado["active"] == 0


def test_existe_gestor(usuarios: User):
    assert usuarios.existe_gestor() is False
    usuarios.criar("Gestor", "gestor@exemplo.com", "hash-falso", "gestor")
    assert usuarios.existe_gestor() is True
