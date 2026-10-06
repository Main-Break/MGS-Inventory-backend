"""Verificações: usuário manda uma foto, a IA conta os itens."""

import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

import config
from models.verification import DataVerification
from neural.neural import ModelUnavailableError, Neural
from schemas import Detection, VerificationOut
from security import current_manager, current_user

router = APIRouter(prefix="/verifications", tags=["verifications"])

_EXTENSOES_VALIDAS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

_neural = Neural(config.MODEL_PATH)


def _get_neural() -> Neural:
    return _neural


def _verifications() -> DataVerification:
    return DataVerification(config.DB_FILE)


def _build_verification(linha: dict) -> dict:
    return {**linha, "detections": [Detection(**d) for d in json.loads(linha["detections"])]}


@router.post("", response_model=VerificationOut, status_code=status.HTTP_201_CREATED)
def create_verification(
    file: UploadFile = File(...),
    item_id: int | None = Form(default=None),
    user: dict = Depends(current_user),
    neural: Neural = Depends(_get_neural),
) -> dict:
    extensao = Path(file.filename or "").suffix.lower()
    if extensao not in _EXTENSOES_VALIDAS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Extensão de imagem não suportada: '{extensao}'.")

    conteudo = file.file.read()
    if not conteudo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Arquivo de imagem vazio.")

    Path(config.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    # Nome gerado aqui, nunca o do cliente: evita path traversal e sobrescrita.
    nome_arquivo = f"{uuid.uuid4().hex}{extensao}"
    (Path(config.UPLOAD_DIR) / nome_arquivo).write_bytes(conteudo)

    try:
        deteccoes = neural.count_items(Path(config.UPLOAD_DIR) / nome_arquivo)
    except ModelUnavailableError as erro:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(erro)) from erro

    _, linha = _verifications().create(user["id"], item_id, nome_arquivo, json.dumps(deteccoes))
    return _build_verification(linha)


@router.get("", response_model=list[VerificationOut])
def list_verifications(user: dict = Depends(current_user)) -> list[dict]:
    verifications = _verifications()

    if user["role"] == "gestor":
        _, linhas = verifications.list_all()
    else:
        _, linhas = verifications.list_by_user(user["id"])

    return [_build_verification(linha) for linha in linhas]


@router.get("/{verification_id}", response_model=VerificationOut)
def get_verification(verification_id: int, user: dict = Depends(current_user)) -> dict:
    sucesso, linha = _verifications().find_by_id(verification_id)

    if not sucesso:
        raise HTTPException(status.HTTP_404_NOT_FOUND, linha)

    if user["role"] != "gestor" and linha["user_id"] != user["id"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sem acesso a essa verificação.")

    return _build_verification(linha)


@router.patch("/{verification_id}/approve", response_model=VerificationOut)
def approve_verification(
    verification_id: int, aprovado: bool, _manager: dict = Depends(current_manager)
) -> dict:
    sucesso, linha = _verifications().approve(verification_id, aprovado)

    if not sucesso:
        raise HTTPException(status.HTTP_404_NOT_FOUND, linha)
    return _build_verification(linha)
