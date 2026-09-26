"""Senha, token e quem pode fazer o quê."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import core
from core import banco

_ITERACOES = 600_000  # recomendação atual da OWASP para PBKDF2-HMAC-SHA256
_esquema = HTTPBearer(auto_error=False)


def gerar_hash_senha(senha: str) -> str:
    salt = secrets.token_bytes(16)
    resumo = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt, _ITERACOES)
    return f"{salt.hex()}${resumo.hex()}"


def conferir_senha(senha: str, hash_salvo: str) -> bool:
    salt_hex, resumo_hex = hash_salvo.split("$")
    resumo = hashlib.pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(salt_hex), _ITERACOES)
    return hmac.compare_digest(resumo.hex(), resumo_hex)  # compare_digest não vaza tempo de resposta


def criar_token(usuario_id: int, papel: str) -> str:
    expira = datetime.now(timezone.utc) + timedelta(hours=8)
    return jwt.encode({"sub": str(usuario_id), "role": papel, "exp": expira}, core.JWT_SECRET, algorithm="HS256")


def usuario_logado(credenciais: HTTPAuthorizationCredentials | None = Depends(_esquema)) -> dict:
    erro = HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido, expirado ou ausente.")
    if credenciais is None:
        raise erro

    try:
        payload = jwt.decode(credenciais.credentials, core.JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise erro from None

    with banco() as db:
        usuario = db.buscar_um("SELECT * FROM users WHERE id = ?", (int(payload["sub"]),))

    if usuario is None or not usuario["active"]:
        raise erro
    return usuario


def gestor_logado(usuario: dict = Depends(usuario_logado)) -> dict:
    if usuario["role"] != "gestor":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Apenas gestores podem fazer isso.")
    return usuario


def criar_gestor_inicial() -> None:
    """Sem isso, ninguém consegue logar na primeira vez (só gestor cria usuário)."""
    with banco() as db:
        if db.buscar_um("SELECT id FROM users WHERE role = 'gestor'") is not None:
            return
        db.executar(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'gestor')",
            (core.ADMIN_NAME, core.ADMIN_EMAIL.lower(), gerar_hash_senha(core.ADMIN_PASSWORD)),
        )
