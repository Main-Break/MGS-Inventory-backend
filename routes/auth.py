"""Login: troca e-mail e senha por um token JWT."""

from fastapi import APIRouter, HTTPException, status

import config
import seguranca
from database import banco
from models.user import Login, Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(dados: Login) -> Token:
    with banco() as db:
        usuario = db.buscar_um(
            "SELECT id, password_hash, role, active FROM users WHERE email = :email",
            {"email": dados.email.lower()},
        )

    # Mesma mensagem para e-mail inexistente e senha errada, para não
    # entregar quais e-mails estão cadastrados.
    if usuario is None or not seguranca.conferir_senha(dados.password, usuario["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos."
        )

    if not usuario["active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário desativado.")

    return Token(
        access_token=seguranca.criar_token(usuario["id"], usuario["role"]),
        expires_in_minutes=config.JWT_EXPIRE_MINUTES,
    )
