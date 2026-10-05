"""Cadastro, listagem e edição de usuários."""

from fastapi import APIRouter, Depends, HTTPException, status

import config
from models.user import EmailAlreadyRegisteredError, User
from schemas import UserCreate, UserOut, UserUpdate
from security import current_manager, current_user, hash_password

router = APIRouter(prefix="/users", tags=["users"])


def _users() -> User:
    return User(config.DB_FILE)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(dados: UserCreate, _manager: dict = Depends(current_manager)) -> dict:
    try:
        return _users().create(dados.name, dados.email.lower(), hash_password(dados.password), dados.role)
    except EmailAlreadyRegisteredError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um usuário com esse e-mail.") from None


@router.get("", response_model=list[UserOut])
def list_users(_manager: dict = Depends(current_manager)) -> list[dict]:
    return _users().list_all()


@router.get("/me", response_model=UserOut)
def my_profile(user: dict = Depends(current_user)) -> dict:
    return user


@router.put("/me", response_model=UserOut)
def update_my_profile(dados: UserUpdate, user: dict = Depends(current_user)) -> dict:
    password_hash = hash_password(dados.password) if dados.password else user["password_hash"]
    return _users().update(user["id"], dados.name, dados.email.lower(), password_hash)


@router.patch("/{user_id}/active", response_model=UserOut)
def set_user_active(user_id: int, ativo: bool, _manager: dict = Depends(current_manager)) -> dict:
    user = _users().set_active(user_id, ativo)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado.")
    return user
