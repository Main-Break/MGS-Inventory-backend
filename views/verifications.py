"""Telas de listagem e aprovação das verificações (mesmas regras de routes/verifications.py)."""

import json

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import FileResponse, RedirectResponse

from core import config, current_user, has_permission, require_permission, templates, verifications, web_context
from models.schemas import Detection

router = APIRouter(prefix="/app/verifications", tags=["interface web"])


def build_verification(row: dict) -> dict:
    return {**row, "detections": [Detection(**detection) for detection in json.loads(row["detections"])]}


@router.get("")
def list_verifications(request: Request, user: dict = Depends(current_user)):
    if has_permission(user, "verifications.view_all"):
        _, rows = verifications.list_all()
    else:
        _, rows = verifications.list_by_user(user["id"])

    result = [build_verification(row) for row in rows]
    return templates.TemplateResponse(request, "verifications/list.html", web_context(user, verifications=result))


@router.get("/foto/{filename}")
def get_photo(filename: str, _user: dict = Depends(current_user)) -> FileResponse:
    # filename sempre vem do próprio banco (gerado pela API no upload), nunca de entrada livre do navegador.
    photo_path = config.UPLOAD_DIR / filename
    if not photo_path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Foto não encontrada.")
    return FileResponse(photo_path)


@router.post("/{verification_id}/approve")
def approve_verification(verification_id: str, approved: bool = Form(...), _user: dict = Depends(require_permission("verifications.approve"))):
    success, result = verifications.approve(verification_id, approved)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, result)
    return RedirectResponse("/app/verifications", status_code=303)
