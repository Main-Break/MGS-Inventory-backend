"""Testa o model DataUser direto no banco, sem passar pela API."""

import pytest

from models.schema import DataSchema
from models.user import DataUser


@pytest.fixture
def users(tmp_path) -> DataUser:
    db_file = str(tmp_path / "teste.db")
    DataSchema(db_file).migrate()
    return DataUser(db_file)


def test_create_and_find_by_email(users: DataUser):
    sucesso, created = users.create("Ana", "ana@exemplo.com", "hash-falso", "funcionario")
    assert sucesso is True
    assert created["id"] is not None

    _, encontrado = users.find_by_email("ana@exemplo.com")
    assert encontrado["name"] == "Ana"


def test_does_not_allow_duplicate_email(users: DataUser):
    users.create("Ana", "ana@exemplo.com", "hash-falso")

    sucesso, mensagem = users.create("Outra Ana", "ana@exemplo.com", "outro-hash")

    assert sucesso is False
    assert "já existe" in mensagem.lower()


def test_set_active_on_missing_user_returns_error(users: DataUser):
    sucesso, mensagem = users.set_active(999, False)

    assert sucesso is False
    assert "não encontrado" in mensagem.lower()


def test_set_active_deactivates_user(users: DataUser):
    _, created = users.create("Ana", "ana@exemplo.com", "hash-falso")

    sucesso, updated = users.set_active(created["id"], False)

    assert sucesso is True
    assert updated["active"] == 0


def test_has_manager(users: DataUser):
    assert users.has_manager() is False
    users.create("Gestor", "gestor@exemplo.com", "hash-falso", "gestor")
    assert users.has_manager() is True
