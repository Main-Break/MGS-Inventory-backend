"""O que a API recebe e devolve."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Papel = Literal["gestor", "funcionario"]


class Login(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Usuario(BaseModel):
    id: int
    name: str
    email: str
    role: Papel
    active: bool


class UsuarioCriar(BaseModel):
    name: str
    email: str
    password: str = Field(min_length=8)
    role: Papel = "funcionario"


class UsuarioAtualizar(BaseModel):
    name: str
    email: str
    password: str | None = None


class Item(BaseModel):
    id: int
    label: str
    name: str
    stock_quantity: int


class ItemCriar(BaseModel):
    label: str = Field(description="Nome exato da classe que o modelo de IA devolve")
    name: str
    stock_quantity: int = 0


class Deteccao(BaseModel):
    label: str
    count: int
    confidence: float


class Verificacao(BaseModel):
    id: int
    user_id: int
    item_id: int | None
    photo_filename: str
    detections: list[Deteccao]
    approved: bool | None
    created_at: datetime
