"""Testa o model Item direto no banco, sem passar pela API."""

import pytest

from models.core import Core
from models.item import Item, LabelJaCadastradoError


@pytest.fixture
def itens(tmp_path) -> Item:
    db_file = str(tmp_path / "teste.db")
    Core(db_file).migrate()
    return Item(db_file)


def test_criar_e_buscar_por_id(itens: Item):
    criado = itens.criar("parafuso_m6", "Parafuso M6", stock_quantity=10)

    assert itens.buscar_por_id(criado["id"])["name"] == "Parafuso M6"


def test_nao_deixa_duplicar_label(itens: Item):
    itens.criar("parafuso_m6", "Parafuso M6")

    with pytest.raises(LabelJaCadastradoError):
        itens.criar("parafuso_m6", "Outro nome")


def test_buscar_filtra_por_termo(itens: Item):
    itens.criar("parafuso_m6", "Parafuso M6")
    itens.criar("porca_m6", "Porca M6")

    resultado = itens.buscar("parafuso")

    assert len(resultado) == 1
    assert resultado[0]["label"] == "parafuso_m6"


def test_buscar_sem_termo_lista_todos(itens: Item):
    itens.criar("parafuso_m6", "Parafuso M6")
    itens.criar("porca_m6", "Porca M6")

    assert len(itens.buscar()) == 2
