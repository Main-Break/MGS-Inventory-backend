"""Testa o model Item direto no banco, sem passar pela API."""

import pytest

from models.item import Item, LabelAlreadyRegisteredError
from models.schema import Schema


@pytest.fixture
def items(tmp_path) -> Item:
    db_file = str(tmp_path / "teste.db")
    Schema(db_file).migrate()
    return Item(db_file)


def test_create_and_find_by_id(items: Item):
    created = items.create("parafuso_m6", "Parafuso M6", stock_quantity=10)

    assert items.find_by_id(created["id"])["name"] == "Parafuso M6"


def test_does_not_allow_duplicate_label(items: Item):
    items.create("parafuso_m6", "Parafuso M6")

    with pytest.raises(LabelAlreadyRegisteredError):
        items.create("parafuso_m6", "Outro nome")


def test_search_filters_by_term(items: Item):
    items.create("parafuso_m6", "Parafuso M6")
    items.create("porca_m6", "Porca M6")

    result = items.search("parafuso")

    assert len(result) == 1
    assert result[0]["label"] == "parafuso_m6"


def test_search_without_term_lists_all(items: Item):
    items.create("parafuso_m6", "Parafuso M6")
    items.create("porca_m6", "Porca M6")

    assert len(items.search()) == 2
