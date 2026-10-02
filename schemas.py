"""O que a API recebe e devolve."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Role = Literal["gestor", "funcionario"]


class Login(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: Role
    active: bool


class UserCreate(BaseModel):
    name: str
    email: str
    password: str = Field(min_length=8)
    role: Role = "funcionario"


class UserUpdate(BaseModel):
    name: str
    email: str
    password: str | None = None


class ItemOut(BaseModel):
    id: int
    label: str
    name: str
    stock_quantity: int


class ItemCreate(BaseModel):
    label: str = Field(description="Nome exato da classe que o modelo de IA devolve")
    name: str
    stock_quantity: int = 0


class Detection(BaseModel):
    label: str
    count: int
    confidence: float


class VerificationOut(BaseModel):
    id: int
    user_id: int
    item_id: int | None
    photo_filename: str
    detections: list[Detection]
    approved: bool | None
    created_at: datetime
