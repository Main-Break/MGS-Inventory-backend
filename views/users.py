"""
Telas de cadastro, listagem e permissões de usuários.

Mesmas regras de routes/users.py: só o gestor cadastra outro gestor, só o
gestor libera e retira permissão, e cada usuário edita os próprios dados em
"Meu perfil" (não existe tela para um usuário editar o cadastro de outro,
porque a API também não tem essa operação).
"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from core import current_manager, current_user, require_permission, templates, user_permissions, users, permissions as permissions_model, web_context
from models.permissions import DataPermission
from util.security import hash_password

router = APIRouter(prefix="/app", tags=["interface web"])


@router.get("/users")
def list_users(request: Request, q: str | None = None, user: dict = Depends(require_permission("users.list"))):
    _, result = users.search(q)
    return templates.TemplateResponse(request, "users/list.html", web_context(user, users=result, termo=q or ""))


@router.get("/users/novo")
def new_user_form(request: Request, user: dict = Depends(require_permission("users.create"))):
    return templates.TemplateResponse(request, "users/form.html", web_context(user, pode_criar_gestor=user["role"] == "gestor"))


@router.post("/users/novo")
def create_user(
    request: Request,
    name: str = Form(...), email: str = Form(...), password: str = Form(...), role: str = Form("funcionario"),
    user: dict = Depends(require_permission("users.create")),
):
    if role == "gestor" and user["role"] != "gestor":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Apenas gestores podem cadastrar outro gestor.")

    success, result = users.create(name, email.lower(), hash_password(password), role)

    if not success:
        context = web_context(user, pode_criar_gestor=user["role"] == "gestor", erro=result)
        return templates.TemplateResponse(request, "users/form.html", context, status_code=409)

    return RedirectResponse("/app/users", status_code=303)


@router.post("/users/{user_id}/status")
def set_user_status(user_id: str, new_status: str = Form(...), user: dict = Depends(require_permission("users.status"))):
    exists, target = users.find_by_id(user_id)
    if not exists:
        raise HTTPException(status.HTTP_404_NOT_FOUND, target)

    if target["role"] == "gestor" and user["role"] != "gestor":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Apenas gestores podem alterar outro gestor.")

    users.set_status(user_id, new_status)
    return RedirectResponse("/app/users", status_code=303)


@router.get("/users/{user_id}/permissoes")
def user_permissions_form(request: Request, user_id: str, manager: dict = Depends(current_manager)):
    exists, target = users.find_by_id(user_id)
    if not exists:
        raise HTTPException(status.HTTP_404_NOT_FOUND, target)

    granted = user_permissions(target)
    context = web_context(manager, usuario_alvo=target, todas_permissoes=DataPermission.PERMISSIONS, concedidas=granted)
    return templates.TemplateResponse(request, "users/permissions.html", context)


@router.post("/users/{user_id}/permissoes/conceder")
def grant_permission(user_id: str, permission: str = Form(...), _manager: dict = Depends(current_manager)):
    permissions_model.grant(user_id, permission)
    return RedirectResponse(f"/app/users/{user_id}/permissoes", status_code=303)


@router.post("/users/{user_id}/permissoes/retirar")
def revoke_permission(user_id: str, permission: str = Form(...), _manager: dict = Depends(current_manager)):
    permissions_model.revoke(user_id, permission)
    return RedirectResponse(f"/app/users/{user_id}/permissoes", status_code=303)


@router.get("/me")
def my_profile_form(request: Request, user: dict = Depends(current_user)):
    return templates.TemplateResponse(request, "users/perfil.html", web_context(user))


@router.post("/me")
def update_my_profile(
    request: Request,
    name: str = Form(...), email: str = Form(...), password: str = Form(""),
    user: dict = Depends(current_user),
):
    password_hash = hash_password(password) if password else user["password_hash"]
    success, result = users.update(user["id"], name, email.lower(), password_hash)

    if not success:
        return templates.TemplateResponse(request, "users/perfil.html", web_context(user, erro=result), status_code=409)

    return RedirectResponse("/app/me", status_code=303)
