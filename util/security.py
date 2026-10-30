"""
Funções de segurança: senha e token de acesso (JWT).

Este arquivo não conhece banco de dados nem rotas, só faz as contas.
Quem usa essas funções para proteger as rotas é o core.py (current_user e current_manager).
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

# Recomendação atual da OWASP para PBKDF2-HMAC-SHA256.
PASSWORD_ITERATIONS = 600_000

# Tempo que o token de acesso vale depois do login.
TOKEN_HOURS = 8


def hash_password(password: str) -> str:
    """Gera o hash da senha com um salt aleatório. Formato salvo: "salt$hash"."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PASSWORD_ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Confere se a senha bate com o hash salvo no banco."""
    salt_hex, digest_hex = stored_hash.split("$")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), PASSWORD_ITERATIONS)

    # compare_digest leva sempre o mesmo tempo, assim a resposta não entrega pistas da senha.
    return hmac.compare_digest(digest.hex(), digest_hex)


def create_token(user_id: str, role: str, secret: str) -> str:
    """Cria o token de acesso entregue no login."""
    expires = datetime.now(timezone.utc) + timedelta(hours=TOKEN_HOURS)
    return jwt.encode({"sub": user_id, "role": role, "exp": expires}, secret, algorithm="HS256")


def read_token(token: str, secret: str) -> str | None:
    """Lê o token e devolve o id do usuário. Se o token for inválido ou estiver vencido, devolve None."""
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None

    return payload.get("sub")
