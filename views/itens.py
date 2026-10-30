"""Telas de cadastro e listagem de itens (mesmas regras de routes/itens.py)."""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from core import current_user, itens, materials, require_permission, templates, web_context

router = APIRouter(prefix="/app/itens", tags=["interface web"])


def item_form_data(
    name: str, description: str, label: str, sku: str, barcode: str, brand: str, category: str, material_id: str,
    unit: str, weight_kg: str, height_cm: str, width_cm: str, length_cm: str, stock_quantity: int, min_stock: int, location: str,
) -> dict:
    """Monta o dicionário coluna -> valor a partir dos campos do formulário (texto vazio e número opcional vazio viram None)."""
    def as_float(value: str) -> float | None:
        return float(value) if value else None

    return {
        "name": name, "description": description or None, "label": label,
        "sku": sku or None, "barcode": barcode or None, "brand": brand or None, "category": category or None,
        "material_id": material_id or None, "unit": unit or "un",
        "weight_kg": as_float(weight_kg), "height_cm": as_float(height_cm),
        "width_cm": as_float(width_cm), "length_cm": as_float(length_cm),
        "stock_quantity": stock_quantity, "min_stock": min_stock, "location": location or None,
    }


def form_context(user: dict, item: dict | None, erro: str | None = None) -> dict:
    _, available_materials = materials.list_all()
    return web_context(user, item=item, materiais=available_materials, erro=erro)


@router.get("")
def list_itens(request: Request, q: str | None = None, user: dict = Depends(current_user)):
    _, result = itens.search(q)
    return templates.TemplateResponse(request, "itens/list.html", web_context(user, itens=result, termo=q or ""))


@router.get("/novo")
def new_item_form(request: Request, user: dict = Depends(require_permission("itens.create"))):
    return templates.TemplateResponse(request, "itens/form.html", form_context(user, item=None))


@router.post("/novo")
def create_item(
    request: Request,
    name: str = Form(...), description: str = Form(""), label: str = Form(...), sku: str = Form(""),
    barcode: str = Form(""), brand: str = Form(""), category: str = Form(""), material_id: str = Form(""),
    unit: str = Form("un"), weight_kg: str = Form(""), height_cm: str = Form(""), width_cm: str = Form(""),
    length_cm: str = Form(""), stock_quantity: int = Form(0), min_stock: int = Form(0), location: str = Form(""),
    user: dict = Depends(require_permission("itens.create")),
):
    data = item_form_data(name, description, label, sku, barcode, brand, category, material_id, unit, weight_kg, height_cm, width_cm, length_cm, stock_quantity, min_stock, location)
    success, result = itens.create(data)

    if not success:
        return templates.TemplateResponse(request, "itens/form.html", form_context(user, item=data, erro=result), status_code=409)

    return RedirectResponse("/app/itens", status_code=303)


@router.get("/{item_id}/editar")
def edit_item_form(request: Request, item_id: str, user: dict = Depends(require_permission("itens.edit"))):
    success, item = itens.find_by_id(item_id)
    if not success:
        return templates.TemplateResponse(request, "erro.html", web_context(user, mensagem=item), status_code=404)

    return templates.TemplateResponse(request, "itens/form.html", form_context(user, item=item))


@router.post("/{item_id}/editar")
def update_item(
    request: Request,
    item_id: str,
    name: str = Form(...), description: str = Form(""), label: str = Form(...), sku: str = Form(""),
    barcode: str = Form(""), brand: str = Form(""), category: str = Form(""), material_id: str = Form(""),
    unit: str = Form("un"), weight_kg: str = Form(""), height_cm: str = Form(""), width_cm: str = Form(""),
    length_cm: str = Form(""), stock_quantity: int = Form(0), min_stock: int = Form(0), location: str = Form(""),
    user: dict = Depends(require_permission("itens.edit")),
):
    data = item_form_data(name, description, label, sku, barcode, brand, category, material_id, unit, weight_kg, height_cm, width_cm, length_cm, stock_quantity, min_stock, location)
    success, result = itens.update(item_id, data)

    if not success:
        return templates.TemplateResponse(request, "itens/form.html", form_context(user, item={**data, "id": item_id}, erro=result), status_code=409)

    return RedirectResponse("/app/itens", status_code=303)


@router.post("/{item_id}/status")
def set_item_status(item_id: str, new_status: str = Form(...), _user: dict = Depends(require_permission("itens.status"))):
    itens.set_status(item_id, new_status)
    return RedirectResponse("/app/itens", status_code=303)
