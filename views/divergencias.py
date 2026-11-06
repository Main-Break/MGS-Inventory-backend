"""
Fila de divergências: itens cujo peso teórico (peças x peso unitário) não bate com
o saldo em quilos do ERP, acima da tolerância (ver models/itens.py::list_with_divergence).

Mesma visão de itens.list, então usa a mesma checagem de acesso (current_user).
"""

from fastapi import APIRouter, Depends, Request

from core import current_user, itens, templates, total_paginas, web_context
from database.database import Database

router = APIRouter(prefix="/app/divergencias", tags=["interface web"])


@router.get("")
def list_divergencias(request: Request, page: int = 1, user: dict = Depends(current_user)):
    # list_with_divergence já calcula e ordena tudo em Python (não é uma consulta simples
    # de tabela), então a página é recortada aqui em vez de LIMIT/OFFSET no banco.
    _, result = itens.list_with_divergence()
    total = len(result)
    inicio = (max(page, 1) - 1) * Database.PAGE_SIZE
    pagina = result[inicio:inicio + Database.PAGE_SIZE]

    return templates.TemplateResponse(request, "divergencias/list.html", web_context(
        user, divergencias=pagina, pagina_atual=page, total_paginas=total_paginas(total), total_registros=total,
    ))
