"""Página inicial da interface web: contadores gerais do sistema."""

from fastapi import APIRouter, Depends, Request

from core import current_user, itens, materials, templates, users, verifications, web_context

router = APIRouter(prefix="/app", tags=["interface web"])


@router.get("")
def dashboard(request: Request, user: dict = Depends(current_user)):
    _, all_users = users.list_all()
    _, all_itens = itens.list_all()
    _, all_materials = materials.list_all()
    _, all_verifications = verifications.list_all()

    pendentes = [v for v in all_verifications if v["approved"] is None]

    context = web_context(
        user,
        total_users=len(all_users),
        total_itens=len(all_itens),
        total_materials=len(all_materials),
        total_verifications=len(all_verifications),
        total_pendentes=len(pendentes),
    )
    return templates.TemplateResponse(request, "dashboard.html", context)
