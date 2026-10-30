"""Telas de listagem, relatório detalhado e aprovação das verificações (mesmas regras de routes/verifications.py)."""

import json

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse

from core import (
    config,
    create_verification_from_photo,
    current_user,
    has_permission,
    itens,
    require_permission,
    templates,
    users,
    verifications,
    web_context,
)
from models.schemas import Detection

router = APIRouter(prefix="/app/verificacoes", tags=["interface web"])


def build_verification(row: dict, users_by_id: dict, itens_by_id: dict) -> dict:
    """Junta a verificação com o nome de quem enviou, o item conferido e o total contado, para a listagem e o relatório."""
    detections = [Detection(**detection) for detection in json.loads(row["detections"])]
    author = users_by_id.get(row["user_id"])
    item = itens_by_id.get(row["item_id"]) if row["item_id"] else None

    return {
        **row,
        "detections": detections,
        "total_count": sum(detection.count for detection in detections),
        "user_name": author["name"] if author else "Usuário removido",
        "item_name": item["name"] if item else None,
    }


def lookup_tables() -> tuple[dict, dict]:
    """Dicionários id -> registro de usuários e itens, para não buscar um por um a cada verificação."""
    _, all_users = users.list_all()
    _, all_itens = itens.list_all()
    return {user["id"]: user for user in all_users}, {item["id"]: item for item in all_itens}


@router.get("")
def list_verifications(request: Request, user: dict = Depends(current_user)):
    if has_permission(user, "verifications.view_all"):
        _, rows = verifications.list_all()
    else:
        _, rows = verifications.list_by_user(user["id"])

    users_by_id, itens_by_id = lookup_tables()
    result = [build_verification(row, users_by_id, itens_by_id) for row in rows]
    return templates.TemplateResponse(request, "verifications/list.html", web_context(user, verifications=result))


@router.get("/foto/{filename}")
def get_photo(filename: str, _user: dict = Depends(current_user)) -> FileResponse:
    # filename sempre vem do próprio banco (gerado pela API no upload), nunca de entrada livre do navegador.
    photo_path = config.UPLOAD_DIR / filename
    if not photo_path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Foto não encontrada.")
    return FileResponse(photo_path)


@router.get("/nova")
def new_verification_form(request: Request, user: dict = Depends(current_user)):
    _, all_itens = itens.search(None)
    return templates.TemplateResponse(request, "verifications/nova.html", web_context(user, itens=all_itens))


@router.post("/nova")
def create_verification_view(
    request: Request,
    arquivo: UploadFile,
    item_id: str = Form(""),
    user: dict = Depends(current_user),
):
    """
    Envio de verificação pela interface web: foto (câmera ou arquivo), com o item
    identificado por leitura de código de barras, busca manual, ou deixado em
    branco (a IA tenta reconhecer só pela foto). Mesma regra de routes/verifications.py
    (core.py::create_verification_from_photo), só a resposta muda: página, não JSON.
    """
    content = arquivo.file.read()
    status_code, result = create_verification_from_photo(user, item_id or None, arquivo.filename, content)

    if status_code != status.HTTP_201_CREATED:
        _, all_itens = itens.search(None)
        context = web_context(user, itens=all_itens, erro=result, item_id_selecionado=item_id)
        return templates.TemplateResponse(request, "verifications/nova.html", context, status_code=status_code)

    return RedirectResponse(f"/app/verificacoes/{result['id']}", status_code=303)


@router.get("/{verification_id}")
def detail_verification(request: Request, verification_id: str, user: dict = Depends(current_user)):
    """Relatório completo de uma verificação: detalhes à esquerda, foto grande à direita."""
    success, row = verifications.find_by_id(verification_id)
    if not success:
        return templates.TemplateResponse(request, "erro.html", web_context(user, mensagem=row), status_code=404)

    if row["user_id"] != user["id"] and not has_permission(user, "verifications.view_all"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sem acesso a essa verificação.")

    users_by_id, itens_by_id = lookup_tables()
    verification = build_verification(row, users_by_id, itens_by_id)
    return templates.TemplateResponse(request, "verifications/detalhe.html", web_context(user, verification=verification))


@router.post("/{verification_id}/approve")
def approve_verification(verification_id: str, approved: bool = Form(...), _user: dict = Depends(require_permission("verifications.approve"))):
    success, result = verifications.approve(verification_id, approved)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, result)
    return RedirectResponse(f"/app/verificacoes/{verification_id}", status_code=303)
