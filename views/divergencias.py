"""
Fila de divergências: itens cujo peso teórico (peças x peso unitário) não bate com
o saldo em quilos do ERP, acima da tolerância (ver models/itens.py::list_with_divergence).

Mesma visão de itens.list, então usa a mesma checagem de acesso (current_user).
"""

from fastapi import APIRouter, Depends, Request

from core import current_user, itens, templates, web_context

router = APIRouter(prefix="/app/divergencias", tags=["interface web"])


@router.get("")
def list_divergencias(request: Request, user: dict = Depends(current_user)):
    _, result = itens.list_with_divergence()
    return templates.TemplateResponse(request, "divergencias/list.html", web_context(user, divergencias=result))
