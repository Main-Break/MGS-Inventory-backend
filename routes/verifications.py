"""Verificações: o usuário manda uma foto e a IA conta os itens."""

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from core import create_verification_from_photo, current_user, has_permission, require_permission, verifications
from models.schemas import Detection, VerificationOut

router = APIRouter(prefix="/verifications", tags=["verifications"])


def build_verification(row: dict) -> dict:
    """O banco guarda as detecções como texto JSON, aqui elas voltam a ser lista."""
    return {**row, "detections": [Detection(**detection) for detection in json.loads(row["detections"])]}


@router.post("", response_model=VerificationOut, status_code=status.HTTP_201_CREATED)
def create_verification(
    file: UploadFile = File(...),
    item_id: str | None = Form(default=None),
    user: dict = Depends(current_user),
) -> dict:
    content = file.file.read()
    status_code, result = create_verification_from_photo(user, item_id, file.filename, content)

    if status_code != status.HTTP_201_CREATED:
        raise HTTPException(status_code, result)
    return build_verification(result)


@router.get("", response_model=list[VerificationOut])
def list_verifications(user: dict = Depends(current_user)) -> list[dict]:
    # Quem tem a permissão vê todas, os outros veem só as próprias.
    if has_permission(user, "verifications.view_all"):
        _, rows = verifications.list_all()
    else:
        _, rows = verifications.list_by_user(user["id"])

    return [build_verification(row) for row in rows]


@router.get("/{verification_id}", response_model=VerificationOut)
def get_verification(verification_id: str, user: dict = Depends(current_user)) -> dict:
    success, row = verifications.find_by_id(verification_id)

    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, row)

    if row["user_id"] != user["id"] and not has_permission(user, "verifications.view_all"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sem acesso a essa verificação.")

    return build_verification(row)


@router.patch("/{verification_id}/approve", response_model=VerificationOut)
def approve_verification(verification_id: str, approved: bool, _user: dict = Depends(require_permission("verifications.approve"))) -> dict:
    success, row = verifications.approve(verification_id, approved)

    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, row)
    return build_verification(row)
