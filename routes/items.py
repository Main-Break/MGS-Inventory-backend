"""Catálogo de itens que a IA reconhece."""

from fastapi import APIRouter, Depends, HTTPException, status

from core import banco
from models import Item, ItemCriar
from security import gestor_logado, usuario_logado

router = APIRouter(prefix="/items", tags=["items"])


@router.post("", response_model=Item, status_code=status.HTTP_201_CREATED)
def criar_item(dados: ItemCriar, _gestor: dict = Depends(gestor_logado)) -> dict:
    with banco() as db:
        if db.buscar_um("SELECT id FROM items WHERE label = ?", (dados.label,)):
            raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um item com esse label.")

        novo_id = db.executar(
            "INSERT INTO items (label, name, stock_quantity) VALUES (?, ?, ?)",
            (dados.label, dados.name, dados.stock_quantity),
        )
        return db.buscar_um("SELECT * FROM items WHERE id = ?", (novo_id,))


@router.get("", response_model=list[Item])
def buscar_itens(q: str | None = None, _usuario: dict = Depends(usuario_logado)) -> list[dict]:
    with banco() as db:
        if q:
            return db.buscar_todos(
                "SELECT * FROM items WHERE name LIKE ? OR label LIKE ? ORDER BY name",
                (f"%{q}%", f"%{q}%"),
            )
        return db.buscar_todos("SELECT * FROM items ORDER BY name")


@router.get("/{item_id}", response_model=Item)
def obter_item(item_id: int, _usuario: dict = Depends(usuario_logado)) -> dict:
    with banco() as db:
        item = db.buscar_um("SELECT * FROM items WHERE id = ?", (item_id,))
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item não encontrado.")
    return item
