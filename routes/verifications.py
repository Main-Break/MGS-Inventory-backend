"""Verificações: o usuário manda uma foto e a IA conta os itens."""

import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from core import config, current_user, has_permission, itens, neural, require_permission, verifications
from models.schemas import Detection, VerificationOut
from neural.neural import ModelUnavailableError, Neural

router = APIRouter(prefix="/verifications", tags=["verifications"])

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def get_neural() -> Neural:
    """Entrega a rede neural para a rota. Fica separado para poder ser trocado por uma versão falsa nos testes."""
    return neural


def build_verification(row: dict) -> dict:
    """O banco guarda as detecções como texto JSON, aqui elas voltam a ser lista."""
    return {**row, "detections": [Detection(**detection) for detection in json.loads(row["detections"])]}


@router.post("", response_model=VerificationOut, status_code=status.HTTP_201_CREATED)
def create_verification(
    file: UploadFile = File(...),
    item_id: str | None = Form(default=None),
    user: dict = Depends(current_user),
    model: Neural = Depends(get_neural),
) -> dict:
    extension = Path(file.filename or "").suffix.lower()
    if extension not in VALID_EXTENSIONS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Extensão de imagem não suportada: '{extension}'.")

    content = file.file.read()
    if not content:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Arquivo de imagem vazio.")

    if item_id:
        exists, message = itens.find_by_id(item_id)
        if not exists:
            raise HTTPException(status.HTTP_404_NOT_FOUND, message)

    # O nome do arquivo é gerado aqui, nunca o enviado pelo cliente: evita sobrescrever arquivos
    # e evita caminhos maliciosos (ex: "../../arquivo").
    filename = f"{uuid.uuid4().hex}{extension}"
    photo_path = config.UPLOAD_DIR / filename
    photo_path.write_bytes(content)

    try:
        detections = model.count_items(photo_path)
    except ModelUnavailableError as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error

    success, result = verifications.create(user["id"], item_id or None, filename, json.dumps(detections))

    if not success:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, result)
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
