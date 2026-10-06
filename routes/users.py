"""Cadastro, listagem e edição de usuários."""

from fastapi import APIRouter, Depends, HTTPException, status

import config
from models.user import DataUser
from schemas import UserCreate, UserOut, UserUpdate
from security import current_manager, current_user, hash_password

router = APIRouter(prefix="/users", tags=["users"])


def _users() -> DataUser:
    return DataUser(config.DB_FILE)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(dados: UserCreate, _manager: dict = Depends(current_manager)) -> dict:
    sucesso, resultado = _users().create(dados.name, dados.email.lower(), hash_password(dados.password), dados.role)

    if not sucesso:
        raise HTTPException(status.HTTP_409_CONFLICT, resultado)
    return resultado


@router.get("", response_model=list[UserOut])
def list_users(_manager: dict = Depends(current_manager)) -> list[dict]:
    _, usuarios = _users().list_all()
    return usuarios


@router.get("/me", response_model=UserOut)
def my_profile(user: dict = Depends(current_user)) -> dict:
    return user


@router.put("/me", response_model=UserOut)
def update_my_profile(dados: UserUpdate, user: dict = Depends(current_user)) -> dict:
    password_hash = hash_password(dados.password) if dados.password else user["password_hash"]
    _, atualizado = _users().update(user["id"], dados.name, dados.email.lower(), password_hash)
    return atualizado


@router.patch("/{user_id}/active", response_model=UserOut)
def set_user_active(user_id: int, ativo: bool, _manager: dict = Depends(current_manager)) -> dict:
    sucesso, resultado = _users().set_active(user_id, ativo)

    if not sucesso:
        raise HTTPException(status.HTTP_404_NOT_FOUND, resultado)
    return resultado
