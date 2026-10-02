"""Catálogo de itens que a IA reconhece."""

from fastapi import APIRouter, Depends, HTTPException, status

import core
from models.item import Item as ItemModel
from models.item import LabelJaCadastradoError
from schemas import Item, ItemCriar
from security import gestor_logado, usuario_logado

router = APIRouter(prefix="/items", tags=["items"])


def _itens() -> ItemModel:
    return ItemModel(core.DB_FILE)


@router.post("", response_model=Item, status_code=status.HTTP_201_CREATED)
def criar_item(dados: ItemCriar, _gestor: dict = Depends(gestor_logado)) -> dict:
    try:
        return _itens().criar(dados.label, dados.name, dados.stock_quantity)
    except LabelJaCadastradoError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um item com esse label.") from None


@router.get("", response_model=list[Item])
def buscar_itens(q: str | None = None, _usuario: dict = Depends(usuario_logado)) -> list[dict]:
    return _itens().buscar(q)


@router.get("/{item_id}", response_model=Item)
def obter_item(item_id: int, _usuario: dict = Depends(usuario_logado)) -> dict:
    item = _itens().buscar_por_id(item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item não encontrado.")
    return item
