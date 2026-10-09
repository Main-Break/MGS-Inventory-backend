"""Operações da tabela items.

Toda função que busca/grava dado devolve (sucesso: bool, dado): em caso de
sucesso, dado é o registro (dict) ou lista; em caso de falha, dado é uma
mensagem pronta pra mostrar pro usuário/cliente da API.
"""

from app.models.database import Database


class DataItem(Database):

    def create(self, label: str, name: str, stock_quantity: int = 0) -> tuple[bool, dict | str]:
        with self:
            if self.query_one("SELECT id FROM items WHERE label = ?", (label,)):
                return False, "Já existe um item com esse label."

            new_id = self.execute(
                "INSERT INTO items (label, name, stock_quantity) VALUES (?, ?, ?)",
                (label, name, stock_quantity),
            )
            return True, self.query_one("SELECT * FROM items WHERE id = ?", (new_id,))

    def find_by_id(self, item_id: int) -> tuple[bool, dict | str]:
        with self:
            item = self.query_one("SELECT * FROM items WHERE id = ?", (item_id,))

        if item is None:
            return False, "Item não encontrado."
        return True, item

    def search(self, term: str | None = None) -> tuple[bool, list[dict]]:
        with self:
            if term:
                resultado = self.query_all(
                    "SELECT * FROM items WHERE name LIKE ? OR label LIKE ? ORDER BY name",
                    (f"%{term}%", f"%{term}%"),
                )
            else:
                resultado = self.query_all("SELECT * FROM items ORDER BY name")

        return True, resultado
