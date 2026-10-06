"""Login: e-mail+senha vira token JWT."""

from fastapi import APIRouter, HTTPException, status

import config
from models.user import DataUser
from schemas import Login, Token
from security import create_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(dados: Login) -> dict:
    sucesso, user = DataUser(config.DB_FILE).find_by_email(dados.email.lower())

    if not sucesso or not verify_password(dados.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha inválidos.")

    if not user["active"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Usuário desativado.")

    return {"access_token": create_token(user["id"], user["role"])}
