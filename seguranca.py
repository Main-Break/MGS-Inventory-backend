"""Senha, token e quem pode fazer o quê.

Senha: PBKDF2-HMAC-SHA256, só com a biblioteca padrão do Python, e o hash
guardado no banco já carrega as iterações e o salt usados.
Token: JWT assinado com JWT_SECRET (HS256).
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import config
from database import banco
from models.user import Usuario

_ITERACOES = 600_000  # recomendação atual da OWASP para PBKDF2-HMAC-SHA256
_esquema_bearer = HTTPBearer(auto_error=False)


def gerar_hash_senha(senha: str) -> str:
    salt = secrets.token_bytes(16)
    resumo = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, _ITERACOES)
    return f"{_ITERACOES}${salt.hex()}${resumo.hex()}"


def conferir_senha(senha: str, hash_salvo: str) -> bool:
    try:
        iteracoes, salt_hex, resumo_hex = hash_salvo.split("$")
        resumo = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), bytes.fromhex(salt_hex), int(iteracoes))
    except (ValueError, TypeError):
        return False
    # compare_digest em vez de == para não vazar a senha pelo tempo de resposta.
    return hmac.compare_digest(resumo.hex(), resumo_hex)


def criar_token(usuario_id: int, papel: str) -> str:
    agora = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(usuario_id),
            "role": papel,
            "iat": agora,
            "exp": agora + timedelta(minutes=config.JWT_EXPIRE_MINUTES),
        },
        config.JWT_SECRET,
        algorithm=config.JWT_ALGORITHM,
    )


def usuario_logado(
    credenciais: HTTPAuthorizationCredentials | None = Depends(_esquema_bearer),
) -> Usuario:
    """Lê o token do cabeçalho Authorization e devolve o usuário do banco."""
    nao_autenticado = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido, expirado ou ausente.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credenciais is None:
        raise nao_autenticado

    try:
        conteudo = jwt.decode(
            credenciais.credentials, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM]
        )
    except jwt.PyJWTError:
        raise nao_autenticado from None

    with banco() as db:
        linha = db.buscar_um(
            "SELECT id, name, email, role, active, created_at FROM users WHERE id = :id",
            {"id": int(conteudo["sub"])},
        )

    # O papel real vem sempre do banco, nunca do que está escrito no token:
    # assim tirar o acesso de alguém tem efeito na hora, sem esperar o token
    # vencer.
    if linha is None or not linha["active"]:
        raise nao_autenticado

    return Usuario(**linha)


def gestor_logado(usuario: Usuario = Depends(usuario_logado)) -> Usuario:
    if usuario.role != "gestor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas gestores podem fazer isso.",
        )
    return usuario
