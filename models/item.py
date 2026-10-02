"""Operações da tabela items."""

from models.database import Database


class LabelAlreadyRegisteredError(Exception):
    pass


class Item(Database):
    def create(self, label: str, name: str, stock_quantity: int = 0) -> dict:
        with self:
            if self.query_one("SELECT id FROM items WHERE label = ?", (label,)):
                raise LabelAlreadyRegisteredError(label)
            new_id = self.execute(
                "INSERT INTO items (label, name, stock_quantity) VALUES (?, ?, ?)",
                (label, name, stock_quantity),
            )
            return self.query_one("SELECT * FROM items WHERE id = ?", (new_id,))

    def find_by_id(self, item_id: int) -> dict | None:
        with self:
            return self.query_one("SELECT * FROM items WHERE id = ?", (item_id,))

    def search(self, term: str | None = None) -> list[dict]:
        with self:
            if term:
                return self.query_all(
                    "SELECT * FROM items WHERE name LIKE ? OR label LIKE ? ORDER BY name",
                    (f"%{term}%", f"%{term}%"),
                )
            return self.query_all("SELECT * FROM items ORDER BY name")
