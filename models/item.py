"""Operações da tabela items."""

from models.database import Database


class LabelJaCadastradoError(Exception):
    pass


class Item(Database):
    def criar(self, label: str, name: str, stock_quantity: int = 0) -> dict:
        with self:
            if self.query_one("SELECT id FROM items WHERE label = ?", (label,)):
                raise LabelJaCadastradoError(label)
            novo_id = self.execute(
                "INSERT INTO items (label, name, stock_quantity) VALUES (?, ?, ?)",
                (label, name, stock_quantity),
            )
            return self.query_one("SELECT * FROM items WHERE id = ?", (novo_id,))

    def buscar_por_id(self, item_id: int) -> dict | None:
        with self:
            return self.query_one("SELECT * FROM items WHERE id = ?", (item_id,))

    def buscar(self, termo: str | None = None) -> list[dict]:
        with self:
            if termo:
                return self.query_all(
                    "SELECT * FROM items WHERE name LIKE ? OR label LIKE ? ORDER BY name",
                    (f"%{termo}%", f"%{termo}%"),
                )
            return self.query_all("SELECT * FROM items ORDER BY name")
