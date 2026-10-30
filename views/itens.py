"""Telas de cadastro, listagem, cálculo de peso e import/export de itens."""

import csv
import io

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import RedirectResponse, Response

from core import current_user, itens, materials, require_permission, templates, web_context
from util.calculo_peso import SHAPES, peso_kg

router = APIRouter(prefix="/app/itens", tags=["interface web"])

# Colunas aceitas na planilha de importação/exportação (ver templates/itens/importar.html).
CSV_COLUMNS = [
    "sku", "name", "label", "material_code", "shape", "height_cm", "width_cm", "length_cm",
    "unit", "stock_quantity", "stock_kg_erp", "min_stock", "location",
]


def item_form_data(
    name: str, description: str, label: str, sku: str, barcode: str, brand: str, category: str, material_id: str,
    unit: str, shape: str, weight_kg: str, height_cm: str, width_cm: str, length_cm: str,
    stock_quantity: int, stock_kg_erp: str, min_stock: int, location: str,
) -> dict:
    """Monta o dicionário coluna -> valor a partir dos campos do formulário (texto vazio e número opcional vazio viram None)."""
    def as_float(value: str) -> float | None:
        return float(value) if value else None

    return {
        "name": name, "description": description or None, "label": label,
        "sku": sku or None, "barcode": barcode or None, "brand": brand or None, "category": category or None,
        "material_id": material_id or None, "unit": unit or "un", "shape": shape or None,
        "weight_kg": as_float(weight_kg), "height_cm": as_float(height_cm),
        "width_cm": as_float(width_cm), "length_cm": as_float(length_cm),
        "stock_quantity": stock_quantity, "stock_kg_erp": as_float(stock_kg_erp),
        "min_stock": min_stock, "location": location or None,
    }


def form_context(user: dict, item: dict | None, erro: str | None = None) -> dict:
    _, available_materials = materials.list_all()
    return web_context(user, item=item, materiais=available_materials, formatos=SHAPES, erro=erro)


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
    unit: str = Form("un"), shape: str = Form(""), weight_kg: str = Form(""), height_cm: str = Form(""), width_cm: str = Form(""),
    length_cm: str = Form(""), stock_quantity: int = Form(0), stock_kg_erp: str = Form(""), min_stock: int = Form(0), location: str = Form(""),
    user: dict = Depends(require_permission("itens.create")),
):
    data = item_form_data(name, description, label, sku, barcode, brand, category, material_id, unit, shape, weight_kg, height_cm, width_cm, length_cm, stock_quantity, stock_kg_erp, min_stock, location)
    success, result = itens.create(data)

    if not success:
        return templates.TemplateResponse(request, "itens/form.html", form_context(user, item=data, erro=result), status_code=409)

    return RedirectResponse("/app/itens", status_code=303)


@router.get("/calcular-peso")
def calcular_peso(
    shape: str, material_id: str, height_cm: float = 0, width_cm: float = 0, length_cm: float = 0,
    _user: dict = Depends(current_user),
) -> dict:
    """Peso teórico (volume x densidade), usado pelo botão "Calcular peso" do formulário (static/js/app.js)."""
    exists, material = materials.find_by_id(material_id)
    if not exists:
        raise HTTPException(status.HTTP_404_NOT_FOUND, material)

    if shape not in SHAPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Formato inválido.")

    peso = peso_kg(shape, float(material["density"]), height_cm, width_cm, length_cm)
    return {"peso_kg": peso}


@router.get("/exportar")
def exportar_itens(_user: dict = Depends(current_user)) -> Response:
    """Baixa todos os itens em CSV, no mesmo formato aceito pela importação."""
    _, rows = itens.list_all()
    materials_by_id = {}
    _, all_materials = materials.list_all()
    for material in all_materials:
        materials_by_id[material["id"]] = material["code"]

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({**row, "material_code": materials_by_id.get(row["material_id"], "")})

    headers = {"Content-Disposition": "attachment; filename=itens.csv"}
    return Response(buffer.getvalue(), media_type="text/csv", headers=headers)


@router.get("/importar")
def importar_form(request: Request, user: dict = Depends(require_permission("itens.create"))):
    return templates.TemplateResponse(request, "itens/importar.html", web_context(user, colunas=CSV_COLUMNS))


@router.post("/importar")
def importar_itens(request: Request, arquivo: UploadFile, user: dict = Depends(require_permission("itens.create"))):
    conteudo = arquivo.file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(conteudo))

    criados, atualizados, erros = 0, 0, []

    for numero, linha in enumerate(reader, start=2):  # linha 1 é o cabeçalho
        data, erro = _parse_csv_row(linha)
        if erro:
            erros.append(f"Linha {numero}: {erro}")
            continue

        existia, _ = itens.find_by_sku(data["sku"]) if data.get("sku") else (False, None)
        success, result = itens.import_row(data)

        if not success:
            erros.append(f"Linha {numero}: {result}")
            continue

        if existia:
            atualizados += 1
        else:
            criados += 1

    context = web_context(user, colunas=CSV_COLUMNS, criados=criados, atualizados=atualizados, erros=erros)
    return templates.TemplateResponse(request, "itens/importar.html", context)


def _parse_csv_row(linha: dict) -> tuple[dict | None, str | None]:
    """Converte uma linha do CSV em dict pronto para itens.import_row(), ou devolve a mensagem de erro."""
    name = (linha.get("name") or "").strip()
    label = (linha.get("label") or "").strip()
    if not name or not label:
        return None, "name e label são obrigatórios."

    material_id = None
    material_code = (linha.get("material_code") or "").strip()
    if material_code:
        exists, material = materials.find_by_code(material_code)
        if not exists:
            return None, f"material_code '{material_code}' não encontrado."
        material_id = material["id"]

    shape = (linha.get("shape") or "").strip() or None
    if shape and shape not in SHAPES:
        return None, f"shape '{shape}' inválido."

    def as_float(value) -> float | None:
        value = (value or "").strip()
        return float(value) if value else None

    def as_int(value, default=0) -> int:
        value = (value or "").strip()
        return int(value) if value else default

    data = {
        "name": name, "label": label, "sku": (linha.get("sku") or "").strip() or None,
        "material_id": material_id, "shape": shape,
        "height_cm": as_float(linha.get("height_cm")), "width_cm": as_float(linha.get("width_cm")),
        "length_cm": as_float(linha.get("length_cm")), "unit": (linha.get("unit") or "un").strip(),
        "stock_quantity": as_int(linha.get("stock_quantity")), "stock_kg_erp": as_float(linha.get("stock_kg_erp")),
        "min_stock": as_int(linha.get("min_stock")), "location": (linha.get("location") or "").strip() or None,
    }
    return data, None


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
    unit: str = Form("un"), shape: str = Form(""), weight_kg: str = Form(""), height_cm: str = Form(""), width_cm: str = Form(""),
    length_cm: str = Form(""), stock_quantity: int = Form(0), stock_kg_erp: str = Form(""), min_stock: int = Form(0), location: str = Form(""),
    user: dict = Depends(require_permission("itens.edit")),
):
    data = item_form_data(name, description, label, sku, barcode, brand, category, material_id, unit, shape, weight_kg, height_cm, width_cm, length_cm, stock_quantity, stock_kg_erp, min_stock, location)
    success, result = itens.update(item_id, data)

    if not success:
        return templates.TemplateResponse(request, "itens/form.html", form_context(user, item={**data, "id": item_id}, erro=result), status_code=409)

    return RedirectResponse("/app/itens", status_code=303)


@router.post("/{item_id}/status")
def set_item_status(item_id: str, new_status: str = Form(...), _user: dict = Depends(require_permission("itens.status"))):
    itens.set_status(item_id, new_status)
    return RedirectResponse("/app/itens", status_code=303)
