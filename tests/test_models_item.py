"""Testa o model DataItem direto no banco, sem passar pela API."""

import pytest

from models.item import DataItem
from models.schema import DataSchema


@pytest.fixture
def items(tmp_path) -> DataItem:
    db_file = str(tmp_path / "teste.db")
    DataSchema(db_file).migrate()
    return DataItem(db_file)


def test_create_and_find_by_id(items: DataItem):
    _, created = items.create("parafuso_m6", "Parafuso M6", stock_quantity=10)

    _, encontrado = items.find_by_id(created["id"])
    assert encontrado["name"] == "Parafuso M6"


def test_does_not_allow_duplicate_label(items: DataItem):
    items.create("parafuso_m6", "Parafuso M6")

    sucesso, mensagem = items.create("parafuso_m6", "Outro nome")

    assert sucesso is False
    assert "já existe" in mensagem.lower()


def test_search_filters_by_term(items: DataItem):
    items.create("parafuso_m6", "Parafuso M6")
    items.create("porca_m6", "Porca M6")

    _, resultado = items.search("parafuso")

    assert len(resultado) == 1
    assert resultado[0]["label"] == "parafuso_m6"


def test_search_without_term_lists_all(items: DataItem):
    items.create("parafuso_m6", "Parafuso M6")
    items.create("porca_m6", "Porca M6")

    _, resultado = items.search()
    assert len(resultado) == 2
