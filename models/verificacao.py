"""Formatos de entrada e saída das verificações (a contagem por foto)."""

from datetime import datetime

from pydantic import BaseModel, Field


class ItemContado(BaseModel):
    item_id: int | None
    label: str
    item_name: str | None
    count: int
    ai_confidence_pct: float  # confiança média que o próprio modelo reporta
    manual_accuracy_pct: float | None  # contagem da IA contra a recontagem manual


class Verificacao(BaseModel):
    id: int
    user_id: int
    user_name: str
    expected_item_id: int | None
    expected_item_label: str | None
    manual_count: int | None
    diverge_do_esperado: bool | None
    approved: bool | None
    approved_by: int | None
    approved_by_name: str | None
    approved_at: datetime | None
    approval_note: str | None
    created_at: datetime
    photos: list[str]
    items: list[ItemContado]


class ContagemManual(BaseModel):
    manual_count: int = Field(ge=0)


class Aprovacao(BaseModel):
    approved: bool
    approval_note: str | None = Field(default=None, max_length=500)
