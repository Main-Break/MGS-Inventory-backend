"""Catálogo de itens do estoque.

O label é o nome exato da classe que o modelo devolve: é por ele que a
contagem da foto se liga ao item cadastrado.
"""

from fastapi import APIRouter, Depends, HTTPException, status

import seguranca
from database import Banco, banco
from models.itens import Item, ItemAtualizar, ItemCriar
from models.user import Usuario

router = APIRouter(prefix="/items", tags=["items"])

_COLUNAS = "id, label, name, stock_quantity, created_at, updated_at"


def _buscar(db: Banco, item_id: int) -> dict | None:
    return db.buscar_um(f"SELECT {_COLUNAS} FROM items WHERE id = :id", {"id": item_id})


def _label_em_uso(db: Banco, label: str, ignorar_id: int | None = None) -> bool:
    linha = db.buscar_um("SELECT id FROM items WHERE label = :label", {"label": label})
    return linha is not None and linha["id"] != ignorar_id


@router.post("", response_model=Item, status_code=status.HTTP_201_CREATED)
def criar_item(dados: ItemCriar, _gestor: Usuario = Depends(seguranca.gestor_logado)) -> Item:
    with banco() as db:
        if _label_em_uso(db, dados.label):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Já existe um item com o label '{dados.label}'.",
            )

        novo_id = db.executar(
            "INSERT INTO items (label, name, stock_quantity) VALUES (:label, :name, :stock_quantity)",
            {"label": dados.label, "name": dados.name, "stock_quantity": dados.stock_quantity},
        )
        return Item(**_buscar(db, novo_id))


@router.get("", response_model=list[Item])
def buscar_itens(q: str | None = None, _usuario: Usuario = Depends(seguranca.usuario_logado)) -> list[Item]:
    """Busca por nome ou label, usada pelo funcionário para escolher o que vai contar."""
    with banco() as db:
        if q:
            linhas = db.buscar_todos(
                f"SELECT {_COLUNAS} FROM items WHERE name LIKE :termo OR label LIKE :termo ORDER BY name",
                {"termo": f"%{q}%"},
            )
        else:
            linhas = db.buscar_todos(f"SELECT {_COLUNAS} FROM items ORDER BY name")
    return [Item(**linha) for linha in linhas]


@router.get("/{item_id}", response_model=Item)
def obter_item(item_id: int, _usuario: Usuario = Depends(seguranca.usuario_logado)) -> Item:
    with banco() as db:
        linha = _buscar(db, item_id)
    if linha is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item {item_id} não encontrado.")
    return Item(**linha)


@router.patch("/{item_id}", response_model=Item)
def atualizar_item(
    item_id: int, dados: ItemAtualizar, _gestor: Usuario = Depends(seguranca.gestor_logado)
) -> Item:
    campos = {"label": dados.label, "name": dados.name, "stock_quantity": dados.stock_quantity}
    campos = {coluna: valor for coluna, valor in campos.items() if valor is not None}

    with banco() as db:
        if _buscar(db, item_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Item {item_id} não encontrado."
            )

        if dados.label and _label_em_uso(db, dados.label, ignorar_id=item_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Já existe um item com o label '{dados.label}'.",
            )

        if campos:
            # Os nomes das colunas vêm daqui de dentro; os valores vão como parâmetro.
            atribuicoes = ", ".join(f"{coluna} = :{coluna}" for coluna in campos)
            db.executar(
                f"UPDATE items SET {atribuicoes}, updated_at = CURRENT_TIMESTAMP WHERE id = :id",
                {**campos, "id": item_id},
            )

        return Item(**_buscar(db, item_id))
