"""Catálogo de itens que a IA reconhece."""

from fastapi import APIRouter, Depends, HTTPException, status

import config
from models.item import Item, LabelAlreadyRegisteredError
from schemas import ItemCreate, ItemOut
from security import current_manager, current_user

router = APIRouter(prefix="/items", tags=["items"])


def _items() -> Item:
    return Item(config.DB_FILE)


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(dados: ItemCreate, _manager: dict = Depends(current_manager)) -> dict:
    try:
        return _items().create(dados.label, dados.name, dados.stock_quantity)
    except LabelAlreadyRegisteredError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um item com esse label.") from None


@router.get("", response_model=list[ItemOut])
def search_items(q: str | None = None, _user: dict = Depends(current_user)) -> list[dict]:
    return _items().search(q)


@router.get("/{item_id}", response_model=ItemOut)
def get_item(item_id: int, _user: dict = Depends(current_user)) -> dict:
    item = _items().find_by_id(item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item não encontrado.")
    return item
