"""Login: e-mail+senha vira token JWT."""

from fastapi import APIRouter, HTTPException, status

from core import banco
from models import Login, Token
from security import conferir_senha, criar_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(dados: Login) -> dict:
    with banco() as db:
        usuario = db.buscar_um("SELECT * FROM users WHERE email = ?", (dados.email.lower(),))

    if usuario is None or not conferir_senha(dados.password, usuario["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha inválidos.")
    if not usuario["active"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Usuário desativado.")

    return {"access_token": criar_token(usuario["id"], usuario["role"])}
