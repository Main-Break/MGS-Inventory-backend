"""
Operações da tabela itens (cadastro usado na verificação de estoque).

Não existe SQL aqui: tudo passa pelas funções da classe mãe Database.

Toda função devolve (sucesso, dado): em caso de sucesso, dado é o registro
(dicionário) ou a lista; em caso de falha, dado é uma mensagem pronta para
mostrar ao usuário.
"""

from database.database import Database


class DataItem(Database):

    TABLE = "itens"

    # Colunas que não podem repetir entre itens, com o nome usado na mensagem de erro.
    UNIQUE_COLUMNS = {"label": "label", "sku": "SKU", "barcode": "código de barras"}

    def find_by_id(self, item_id: str) -> tuple[bool, dict | str]:
        success, item = self.select_one(self.TABLE, "id", item_id)

        if not success or item is None:
            return False, "Item não encontrado."
        return True, item

    def check_duplicate(self, data: dict, item_id: str | None = None) -> str | None:
        """
        Confere se label, SKU ou código de barras já pertencem a outro item.
        Retorna a mensagem de erro, ou None se estiver tudo certo.
        item_id é o próprio item na edição, para ele não ser comparado com ele mesmo.
        """
        for column, text in self.UNIQUE_COLUMNS.items():
            value = data.get(column)
            if not value:
                continue

            _, other = self.select_one(self.TABLE, column, value)
            if other is not None and other["id"] != item_id:
                return f"Já existe um item com esse {text}."

        return None

    def clean(self, data: dict) -> dict:
        """Texto vazio vira None, para não ocupar o valor único de SKU e código de barras."""
        return {column: (None if value == "" else value) for column, value in data.items()}

    def create(self, data: dict) -> tuple[bool, dict | str]:
        """
        Cadastra um item. data é um dicionário coluna -> valor, já validado pelo
        ItemData de models/schemas.py.
        """
        data = self.clean(data)

        duplicate = self.check_duplicate(data)
        if duplicate:
            return False, duplicate

        success, new_id = self.insert_table(self.TABLE, list(data.keys()), list(data.values()))

        if not success:
            return False, "Não foi possível cadastrar o item."
        return self.find_by_id(new_id)

    def update(self, item_id: str, data: dict) -> tuple[bool, dict | str]:
        exists, message = self.find_by_id(item_id)
        if not exists:
            return False, message

        data = self.clean(data)

        duplicate = self.check_duplicate(data, item_id)
        if duplicate:
            return False, duplicate

        success, _ = self.update_table(self.TABLE, list(data.keys()), list(data.values()), "id", item_id)

        if not success:
            return False, "Não foi possível atualizar o item."
        return self.find_by_id(item_id)

    def set_status(self, item_id: str, status: str) -> tuple[bool, dict | str]:
        """Muda o status: 'active', 'disable' ou 'deleted' (soft delete)."""
        exists, message = self.find_by_id(item_id)
        if not exists:
            return False, message

        self.update_table(self.TABLE, ["status"], [status], "id", item_id)
        return self.find_by_id(item_id)

    def list_all(self) -> tuple[bool, list]:
        return self.select_all(self.TABLE, order_by="name")

    def search(self, term: str | None = None) -> tuple[bool, list]:
        if not term:
            return self.list_all()
        return self.search_data(self.TABLE, ["name", "label", "sku", "barcode"], term, order_by="name")
