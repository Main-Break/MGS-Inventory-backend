"""Cadastro, listagem e edição de usuários, e as permissões de cada um."""

from fastapi import APIRouter, Depends, HTTPException, status

from core import current_manager, current_user, permissions, require_permission, user_permissions, users
from models.permissions import DataPermission
from models.schemas import MyProfileOut, Status, UserCreate, UserOut, UserUpdate
from util.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate, user: dict = Depends(require_permission("users.create"))) -> dict:
    # Só o gestor cria outro gestor, senão um funcionário com essa permissão viraria gestor.
    if data.role == "gestor" and user["role"] != "gestor":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Apenas gestores podem cadastrar outro gestor.")

    success, result = users.create(data.name, data.email.lower(), hash_password(data.password), data.role)

    if not success:
        raise HTTPException(status.HTTP_409_CONFLICT, result)
    return result


@router.get("", response_model=list[UserOut])
def list_users(q: str | None = None, _user: dict = Depends(require_permission("users.list"))) -> list[dict]:
    _, result = users.search(q)
    return result


@router.get("/me", response_model=MyProfileOut)
def my_profile(user: dict = Depends(current_user)) -> dict:
    return {**user, "permissions": user_permissions(user)}


@router.put("/me", response_model=UserOut)
def update_my_profile(data: UserUpdate, user: dict = Depends(current_user)) -> dict:
    # Sem senha nova, mantém a senha atual.
    password_hash = hash_password(data.password) if data.password else user["password_hash"]

    success, result = users.update(user["id"], data.name, data.email.lower(), password_hash)

    if not success:
        raise HTTPException(status.HTTP_409_CONFLICT, result)
    return result


@router.patch("/{user_id}/status", response_model=UserOut)
def set_user_status(user_id: str, new_status: Status, user: dict = Depends(require_permission("users.status"))) -> dict:
    exists, target = users.find_by_id(user_id)
    if not exists:
        raise HTTPException(status.HTTP_404_NOT_FOUND, target)

    # Quem não é gestor não mexe na conta de um gestor.
    if target["role"] == "gestor" and user["role"] != "gestor":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Apenas gestores podem alterar outro gestor.")

    _, result = users.set_status(user_id, new_status)
    return result


# ----------------------------------------------------------------------------
# Permissões: só o gestor libera e retira, isso não pode ser delegado.
# ----------------------------------------------------------------------------
@router.get("/permissions/available", response_model=dict[str, str])
def available_permissions(_user: dict = Depends(current_user)) -> dict:
    """Todas as permissões que podem ser liberadas, com a descrição de cada uma."""
    return DataPermission.PERMISSIONS


@router.get("/{user_id}/permissions", response_model=list[str])
def get_user_permissions(user_id: str, _manager: dict = Depends(current_manager)) -> list:
    exists, target = users.find_by_id(user_id)
    if not exists:
        raise HTTPException(status.HTTP_404_NOT_FOUND, target)

    return user_permissions(target)


@router.post("/{user_id}/permissions/{permission}", response_model=list[str])
def grant_permission(user_id: str, permission: str, _manager: dict = Depends(current_manager)) -> list:
    exists, target = users.find_by_id(user_id)
    if not exists:
        raise HTTPException(status.HTTP_404_NOT_FOUND, target)

    success, result = permissions.grant(user_id, permission)

    if not success:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, result)
    return result


@router.delete("/{user_id}/permissions/{permission}", response_model=list[str])
def revoke_permission(user_id: str, permission: str, _manager: dict = Depends(current_manager)) -> list:
    exists, target = users.find_by_id(user_id)
    if not exists:
        raise HTTPException(status.HTTP_404_NOT_FOUND, target)

    success, result = permissions.revoke(user_id, permission)

    if not success:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, result)
    return result
