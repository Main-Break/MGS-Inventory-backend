"""Verificações: usuário manda uma foto, a IA conta os itens."""

import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

import core
from models.verification import Verification
from neural.neural import ModeloIndisponivelError, Neural
from schemas import Deteccao, Verificacao
from security import gestor_logado, usuario_logado

router = APIRouter(prefix="/verifications", tags=["verifications"])

_EXTENSOES_VALIDAS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

_neural = Neural(core.MODEL_PATH)


def _obter_neural() -> Neural:
    return _neural


def _verificacoes() -> Verification:
    return Verification(core.DB_FILE)


def _montar_verificacao(linha: dict) -> dict:
    return {**linha, "detections": [Deteccao(**d) for d in json.loads(linha["detections"])]}


@router.post("", response_model=Verificacao, status_code=status.HTTP_201_CREATED)
def criar_verificacao(
    file: UploadFile = File(...),
    item_id: int | None = Form(default=None),
    usuario: dict = Depends(usuario_logado),
    neural: Neural = Depends(_obter_neural),
) -> dict:
    extensao = Path(file.filename or "").suffix.lower()
    if extensao not in _EXTENSOES_VALIDAS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Extensão de imagem não suportada: '{extensao}'.")

    conteudo = file.file.read()
    if not conteudo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Arquivo de imagem vazio.")

    Path(core.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    # Nome gerado aqui, nunca o do cliente: evita path traversal e sobrescrita.
    nome_arquivo = f"{uuid.uuid4().hex}{extensao}"
    (Path(core.UPLOAD_DIR) / nome_arquivo).write_bytes(conteudo)

    try:
        deteccoes = neural.contar_itens(Path(core.UPLOAD_DIR) / nome_arquivo)
    except ModeloIndisponivelError as erro:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(erro)) from erro

    linha = _verificacoes().criar(usuario["id"], item_id, nome_arquivo, json.dumps(deteccoes))
    return _montar_verificacao(linha)


@router.get("", response_model=list[Verificacao])
def listar_verificacoes(usuario: dict = Depends(usuario_logado)) -> list[dict]:
    verificacoes = _verificacoes()
    if usuario["role"] == "gestor":
        linhas = verificacoes.listar_todas()
    else:
        linhas = verificacoes.listar_por_usuario(usuario["id"])
    return [_montar_verificacao(linha) for linha in linhas]


@router.get("/{verificacao_id}", response_model=Verificacao)
def obter_verificacao(verificacao_id: int, usuario: dict = Depends(usuario_logado)) -> dict:
    linha = _verificacoes().buscar_por_id(verificacao_id)
    if linha is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Verificação não encontrada.")
    if usuario["role"] != "gestor" and linha["user_id"] != usuario["id"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sem acesso a essa verificação.")
    return _montar_verificacao(linha)


@router.patch("/{verificacao_id}/approve", response_model=Verificacao)
def aprovar_verificacao(verificacao_id: int, aprovado: bool, _gestor: dict = Depends(gestor_logado)) -> dict:
    linha = _verificacoes().aprovar(verificacao_id, aprovado)
    if linha is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Verificação não encontrada.")
    return _montar_verificacao(linha)
