"""Formatos de entrada e saída dos usuários (o que a API recebe e devolve)."""

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Papel = Literal["gestor", "funcionario"]

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validar_email(email: str | None) -> str | None:
    if email is None:
        return None
    if not _EMAIL.match(email):
        raise ValueError("e-mail inválido")
    return email.lower()


class Usuario(BaseModel):
    """Usuário como a API devolve (a senha nunca sai daqui)."""

    id: int
    name: str
    email: str
    role: Papel
    active: bool
    created_at: datetime


class UsuarioCriar(BaseModel):
    """Usado pelo gestor para cadastrar alguém."""

    name: str = Field(max_length=255)
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: Papel = "funcionario"

    _email = field_validator("email")(_validar_email)


class UsuarioAtualizar(BaseModel):
    """O próprio usuário mexe só nos dados dele, nunca no papel nem no acesso."""

    name: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)

    _email = field_validator("email")(_validar_email)


class UsuarioAtivo(BaseModel):
    active: bool


class Login(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
