"""Cadastro dos itens do estoque que a IA reconhece nas fotos."""

from fastapi import APIRouter, Depends, HTTPException, status

from core import current_user, require_permission, itens, materials
from models.schemas import ItemData, ItemOut, Status

router = APIRouter(prefix="/itens", tags=["itens"])


def check_material(data: ItemData) -> None:
    """O material é opcional, mas se for informado precisa existir."""
    if data.material_id:
        exists, message = materials.find_by_id(data.material_id)
        if not exists:
            raise HTTPException(status.HTTP_404_NOT_FOUND, message)


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(data: ItemData, _user: dict = Depends(require_permission("itens.create"))) -> dict:
    check_material(data)
    success, result = itens.create(data.model_dump())

    if not success:
        raise HTTPException(status.HTTP_409_CONFLICT, result)
    return result


@router.get("", response_model=list[ItemOut])
def search_itens(q: str | None = None, _user: dict = Depends(current_user)) -> list[dict]:
    _, result = itens.search(q)
    return result


@router.get("/{item_id}", response_model=ItemOut)
def get_item(item_id: str, _user: dict = Depends(current_user)) -> dict:
    success, result = itens.find_by_id(item_id)

    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, result)
    return result


@router.put("/{item_id}", response_model=ItemOut)
def update_item(item_id: str, data: ItemData, _user: dict = Depends(require_permission("itens.edit"))) -> dict:
    check_material(data)
    success, result = itens.update(item_id, data.model_dump())

    if not success:
        raise HTTPException(status.HTTP_409_CONFLICT, result)
    return result


@router.patch("/{item_id}/status", response_model=ItemOut)
def set_item_status(item_id: str, new_status: Status, _user: dict = Depends(require_permission("itens.status"))) -> dict:
    success, result = itens.set_status(item_id, new_status)

    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, result)
    return result
