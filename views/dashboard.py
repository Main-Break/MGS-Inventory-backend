"""Página inicial da interface web: contadores e gráficos gerais do sistema."""

from fastapi import APIRouter, Depends, Request

from core import current_user, itens, materials, templates, users, verifications, web_context

router = APIRouter(prefix="/app", tags=["interface web"])


def itens_por_material(all_itens: list, all_materials: list) -> dict:
    """Quantidade de itens ativos por sigla de material, para o gráfico de barras do dashboard."""
    nome_por_id = {material["id"]: material["code"] for material in all_materials}

    contagem: dict[str, int] = {}
    for item in all_itens:
        if item["status"] != "active":
            continue
        sigla = nome_por_id.get(item["material_id"], "Sem material")
        contagem[sigla] = contagem.get(sigla, 0) + 1

    return dict(sorted(contagem.items(), key=lambda par: par[1], reverse=True))


@router.get("")
def dashboard(request: Request, user: dict = Depends(current_user)):
    _, all_users = users.list_all()
    _, all_itens = itens.list_all()
    _, all_materials = materials.list_all()
    _, all_verifications = verifications.list_all()
    _, divergencias = itens.list_with_divergence()

    pendentes = [v for v in all_verifications if v["approved"] is None]
    aprovadas = [v for v in all_verifications if v["approved"] is True]
    reprovadas = [v for v in all_verifications if v["approved"] is False]

    top_divergencias = divergencias[:5]

    context = web_context(
        user,
        total_users=len(all_users),
        total_itens=len(all_itens),
        total_materials=len(all_materials),
        total_verifications=len(all_verifications),
        total_pendentes=len(pendentes),
        total_divergencias=len(divergencias),
        grafico_materiais=itens_por_material(all_itens, all_materials),
        grafico_verificacoes={"Pendentes": len(pendentes), "Aprovadas": len(aprovadas), "Reprovadas": len(reprovadas)},
        grafico_divergencias={item["name"]: abs(item["divergencia_kg"]) for item in top_divergencias},
    )
    return templates.TemplateResponse(request, "dashboard.html", context)
