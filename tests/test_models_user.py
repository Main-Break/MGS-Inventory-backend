"""Testa o model User direto no banco, sem passar pela API."""

import pytest

from models.schema import Schema
from models.user import EmailAlreadyRegisteredError, User


@pytest.fixture
def users(tmp_path) -> User:
    db_file = str(tmp_path / "teste.db")
    Schema(db_file).migrate()
    return User(db_file)


def test_create_and_find_by_email(users: User):
    created = users.create("Ana", "ana@exemplo.com", "hash-falso", "funcionario")

    assert created["id"] is not None
    assert users.find_by_email("ana@exemplo.com")["name"] == "Ana"


def test_does_not_allow_duplicate_email(users: User):
    users.create("Ana", "ana@exemplo.com", "hash-falso")

    with pytest.raises(EmailAlreadyRegisteredError):
        users.create("Outra Ana", "ana@exemplo.com", "outro-hash")


def test_set_active_on_missing_user_returns_none(users: User):
    assert users.set_active(999, False) is None


def test_set_active_deactivates_user(users: User):
    created = users.create("Ana", "ana@exemplo.com", "hash-falso")

    updated = users.set_active(created["id"], False)

    assert updated["active"] == 0


def test_has_manager(users: User):
    assert users.has_manager() is False
    users.create("Gestor", "gestor@exemplo.com", "hash-falso", "gestor")
    assert users.has_manager() is True
