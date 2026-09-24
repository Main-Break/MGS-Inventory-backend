"""Formatos de entrada e saída do catálogo de itens do estoque."""

from datetime import datetime

from pydantic import BaseModel, Field


class Item(BaseModel):
    id: int
    label: str
    name: str
    stock_quantity: int
    created_at: datetime
    updated_at: datetime


class ItemCriar(BaseModel):
    label: str = Field(max_length=100, description="Nome exato da classe que o modelo devolve")
    name: str = Field(max_length=255)
    stock_quantity: int = Field(default=0, ge=0)


class ItemAtualizar(BaseModel):
    label: str | None = Field(default=None, max_length=100)
    name: str | None = Field(default=None, max_length=255)
    stock_quantity: int | None = Field(default=None, ge=0)
