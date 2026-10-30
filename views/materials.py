"""Telas de cadastro e listagem de materiais (mesmas regras de routes/materials.py)."""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from core import current_user, materials, require_permission, templates, web_context

router = APIRouter(prefix="/app/materiais", tags=["interface web"])


@router.get("")
def list_materials(request: Request, q: str | None = None, user: dict = Depends(current_user)):
    _, result = materials.search(q)
    return templates.TemplateResponse(request, "materials/list.html", web_context(user, materials=result, termo=q or ""))


@router.get("/novo")
def new_material_form(request: Request, user: dict = Depends(require_permission("materials.create"))):
    return templates.TemplateResponse(request, "materials/form.html", web_context(user, material=None))


@router.post("/novo")
def create_material(
    request: Request,
    code: str = Form(...),
    name: str = Form(...),
    density: float = Form(...),
    description: str = Form(""),
    user: dict = Depends(require_permission("materials.create")),
):
    data = {"code": code, "name": name, "density": density, "description": description or None}
    success, result = materials.create(data)

    if not success:
        context = web_context(user, material=data, erro=result)
        return templates.TemplateResponse(request, "materials/form.html", context, status_code=409)

    return RedirectResponse("/app/materiais", status_code=303)


@router.get("/{material_id}/editar")
def edit_material_form(request: Request, material_id: str, user: dict = Depends(require_permission("materials.edit"))):
    success, material = materials.find_by_id(material_id)
    if not success:
        return templates.TemplateResponse(request, "erro.html", web_context(user, mensagem=material), status_code=404)

    return templates.TemplateResponse(request, "materials/form.html", web_context(user, material=material))


@router.post("/{material_id}/editar")
def update_material(
    request: Request,
    material_id: str,
    code: str = Form(...),
    name: str = Form(...),
    density: float = Form(...),
    description: str = Form(""),
    user: dict = Depends(require_permission("materials.edit")),
):
    data = {"code": code, "name": name, "density": density, "description": description or None}
    success, result = materials.update(material_id, data)

    if not success:
        context = web_context(user, material={**data, "id": material_id}, erro=result)
        return templates.TemplateResponse(request, "materials/form.html", context, status_code=409)

    return RedirectResponse("/app/materiais", status_code=303)


@router.post("/{material_id}/status")
def set_material_status(material_id: str, new_status: str = Form(...), _user: dict = Depends(require_permission("materials.status"))):
    materials.set_status(material_id, new_status)
    return RedirectResponse("/app/materiais", status_code=303)
