"""Senha, token e quem pode fazer o quê."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import config
from models.user import User

_ITERACOES = 600_000  # recomendação atual da OWASP para PBKDF2-HMAC-SHA256
_esquema = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERACOES)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    salt_hex, digest_hex = stored_hash.split("$")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), _ITERACOES)
    return hmac.compare_digest(digest.hex(), digest_hex)  # compare_digest não vaza tempo de resposta


def create_token(user_id: int, role: str) -> str:
    expira = datetime.now(timezone.utc) + timedelta(hours=8)
    return jwt.encode({"sub": str(user_id), "role": role, "exp": expira}, config.JWT_SECRET, algorithm="HS256")


def current_user(credenciais: HTTPAuthorizationCredentials | None = Depends(_esquema)) -> dict:
    erro = HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido, expirado ou ausente.")
    if credenciais is None:
        raise erro

    try:
        payload = jwt.decode(credenciais.credentials, config.JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise erro from None

    user = User(config.DB_FILE).find_by_id(int(payload["sub"]))

    if user is None or not user["active"]:
        raise erro
    return user


def current_manager(user: dict = Depends(current_user)) -> dict:
    if user["role"] != "gestor":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Apenas gestores podem fazer isso.")
    return user


def create_initial_manager() -> None:
    """Sem isso, ninguém consegue logar na primeira vez (só gestor cria usuário)."""
    users = User(config.DB_FILE)
    if users.has_manager():
        return
    users.create(config.ADMIN_NAME, config.ADMIN_EMAIL.lower(), hash_password(config.ADMIN_PASSWORD), "gestor")
