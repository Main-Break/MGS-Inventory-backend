"""Login: e-mail e senha viram um token de acesso (JWT)."""

from fastapi import APIRouter, HTTPException, status

from core import config, users
from models.schemas import Login, Token
from util.security import create_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(data: Login) -> dict:
    success, user = users.find_by_email(data.email.lower())

    # Mesma mensagem para e-mail ou senha errados, para não revelar quais e-mails existem.
    if not success or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha inválidos.")

    if user["status"] != "active":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Usuário desativado.")

    return {"access_token": create_token(user["id"], user["role"], config.JWT_SECRET)}
