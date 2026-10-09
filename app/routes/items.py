"""Catálogo de itens que a IA reconhece."""

from fastapi import APIRouter, Depends, HTTPException, status

import config
from app.models.item import DataItem
from app.schemas import ItemCreate, ItemOut
from app.util.security import current_manager, current_user

router = APIRouter(prefix="/items", tags=["items"])


def _items() -> DataItem:
    return DataItem(config.DB_FILE)


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(dados: ItemCreate, _manager: dict = Depends(current_manager)) -> dict:
    sucesso, resultado = _items().create(dados.label, dados.name, dados.stock_quantity)

    if not sucesso:
        raise HTTPException(status.HTTP_409_CONFLICT, resultado)
    return resultado


@router.get("", response_model=list[ItemOut])
def search_items(q: str | None = None, _user: dict = Depends(current_user)) -> list[dict]:
    _, resultados = _items().search(q)
    return resultados


@router.get("/{item_id}", response_model=ItemOut)
def get_item(item_id: int, _user: dict = Depends(current_user)) -> dict:
    sucesso, resultado = _items().find_by_id(item_id)

    if not sucesso:
        raise HTTPException(status.HTTP_404_NOT_FOUND, resultado)
    return resultado
