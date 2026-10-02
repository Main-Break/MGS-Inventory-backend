"""Login: e-mail+senha vira token JWT."""

from fastapi import APIRouter, HTTPException, status

import core
from models.user import User
from schemas import Login, Token
from security import conferir_senha, criar_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(dados: Login) -> dict:
    usuario = User(core.DB_FILE).buscar_por_email(dados.email.lower())

    if usuario is None or not conferir_senha(dados.password, usuario["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha inválidos.")
    if not usuario["active"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Usuário desativado.")

    return {"access_token": criar_token(usuario["id"], usuario["role"])}
