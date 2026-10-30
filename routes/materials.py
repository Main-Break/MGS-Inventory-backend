"""Cadastro dos materiais de que os itens são feitos (PEAD, PP, POM, Nylon...)."""

from fastapi import APIRouter, Depends, HTTPException, status

from core import current_user, require_permission, materials
from models.schemas import MaterialData, MaterialOut, Status

router = APIRouter(prefix="/materials", tags=["materials"])


@router.post("", response_model=MaterialOut, status_code=status.HTTP_201_CREATED)
def create_material(data: MaterialData, _user: dict = Depends(require_permission("materials.create"))) -> dict:
    success, result = materials.create(data.model_dump())

    if not success:
        raise HTTPException(status.HTTP_409_CONFLICT, result)
    return result


@router.get("", response_model=list[MaterialOut])
def search_materials(q: str | None = None, _user: dict = Depends(current_user)) -> list[dict]:
    _, result = materials.search(q)
    return result


@router.get("/{material_id}", response_model=MaterialOut)
def get_material(material_id: str, _user: dict = Depends(current_user)) -> dict:
    success, result = materials.find_by_id(material_id)

    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, result)
    return result


@router.put("/{material_id}", response_model=MaterialOut)
def update_material(material_id: str, data: MaterialData, _user: dict = Depends(require_permission("materials.edit"))) -> dict:
    success, result = materials.update(material_id, data.model_dump())

    if not success:
        raise HTTPException(status.HTTP_409_CONFLICT, result)
    return result


@router.patch("/{material_id}/status", response_model=MaterialOut)
def set_material_status(material_id: str, new_status: Status, _user: dict = Depends(require_permission("materials.status"))) -> dict:
    success, result = materials.set_status(material_id, new_status)

    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, result)
    return result
