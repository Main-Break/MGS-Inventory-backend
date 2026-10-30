"""
Formato dos dados que a API recebe e devolve (validação com Pydantic).

Os limites de tamanho (max_length) batem com o tamanho das colunas em
database/database.sql, para o dado ser recusado aqui antes de chegar ao banco.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# Valores aceitos, os mesmos dos ENUM do banco.
Role = Literal["gestor", "funcionario"]
Status = Literal["active", "disable", "deleted"]


# ----------------------------------------------------------------------------
# Login
# ----------------------------------------------------------------------------
class Login(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ----------------------------------------------------------------------------
# Usuários
# ----------------------------------------------------------------------------
class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8)
    role: Role = "funcionario"


class UserUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    password: str | None = Field(default=None, min_length=8)


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: Role
    status: Status


class MyProfileOut(UserOut):
    """O próprio usuário também recebe as permissões, para o front saber quais botões mostrar."""
    permissions: list[str]


# ----------------------------------------------------------------------------
# Materiais (de que os itens são feitos)
# ----------------------------------------------------------------------------
class MaterialData(BaseModel):
    """Campos do material que podem ser informados no cadastro e na edição."""

    code: str = Field(min_length=1, max_length=20, description="Sigla do material (PEAD, PP, POM, NYLON...)")
    name: str = Field(min_length=1, max_length=100, description="Nome completo do material")
    density: float = Field(gt=0, le=999, description="Peso específico em g/cm³, usado nas equações de peso")
    description: str | None = Field(default=None, description="Observações sobre o material")


class MaterialOut(MaterialData):
    id: str
    status: Status
    created_at: datetime
    updated_at: datetime


# ----------------------------------------------------------------------------
# Itens (cadastro usado na verificação de estoque)
# ----------------------------------------------------------------------------
class ItemData(BaseModel):
    """Campos do item que podem ser informados no cadastro e na edição."""

    # Identificação
    name: str = Field(min_length=1, max_length=255, description="Nome do item")
    description: str | None = Field(default=None, description="Descrição detalhada")
    label: str = Field(min_length=1, max_length=100, description="Nome exato da classe que o modelo de IA devolve")
    sku: str | None = Field(default=None, max_length=100, description="Código interno do item")
    barcode: str | None = Field(default=None, max_length=50, description="Código de barras (EAN, GTIN...)")
    brand: str | None = Field(default=None, max_length=100, description="Marca ou fabricante")
    category: str | None = Field(default=None, max_length=100, description="Categoria ou grupo do item")
    material_id: str | None = Field(default=None, description="Id do material de que o item é feito (ver /materials)")

    # Medidas físicas
    unit: str = Field(default="un", min_length=1, max_length=20, description="Unidade de contagem (un, cx, pct, kg...)")
    weight_kg: float | None = Field(default=None, ge=0, description="Peso em quilos")
    height_cm: float | None = Field(default=None, ge=0, description="Altura em centímetros")
    width_cm: float | None = Field(default=None, ge=0, description="Largura em centímetros")
    length_cm: float | None = Field(default=None, ge=0, description="Comprimento em centímetros")

    # Estoque
    stock_quantity: int = Field(default=0, ge=0, description="Quantidade atual")
    min_stock: int = Field(default=0, ge=0, description="Quantidade mínima desejada")
    location: str | None = Field(default=None, max_length=100, description="Onde fica guardado (galpão, prateleira...)")


class ItemOut(ItemData):
    id: str
    status: Status
    created_at: datetime
    updated_at: datetime


# ----------------------------------------------------------------------------
# Verificações (fotos conferidas pela IA)
# ----------------------------------------------------------------------------
class Detection(BaseModel):
    label: str
    count: int
    confidence: float


class VerificationOut(BaseModel):
    id: str
    user_id: str
    item_id: str | None
    photo_filename: str
    detections: list[Detection]
    approved: bool | None
    created_at: datetime
