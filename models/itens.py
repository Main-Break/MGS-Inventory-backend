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

    # Diferença entre o peso teórico (peças x peso unitário) e o saldo em quilos do
    # ERP acima da qual o item entra na fila de divergências (ver list_with_divergence).
    TOLERANCIA_DIVERGENCIA = 0.05  # 5%

    def find_by_id(self, item_id: str) -> tuple[bool, dict | str]:
        success, item = self.select_one(self.TABLE, "id", item_id)

        if not success or item is None:
            return False, "Item não encontrado."
        return True, item

    def find_by_sku(self, sku: str) -> tuple[bool, dict | str]:
        success, item = self.select_one(self.TABLE, "sku", sku)

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

    def import_row(self, data: dict) -> tuple[bool, dict | str]:
        """
        Cria ou atualiza um item a partir de uma linha de planilha (ver
        views/itens.py, importação por CSV). Atualiza pelo SKU quando ele já existe,
        cria um item novo quando não existe ou quando a linha não informa SKU.
        """
        sku = data.get("sku")

        if sku:
            exists, existing = self.find_by_sku(sku)
            if exists:
                return self.update(existing["id"], data)

        return self.create(data)

    def list_with_divergence(self) -> tuple[bool, list]:
        """
        Itens ativos com peso unitário (weight_kg) e saldo do ERP (stock_kg_erp)
        cadastrados, comparando o peso teórico do estoque (peças x peso unitário)
        com o saldo em quilos do ERP. Só entra na lista quem passa de
        TOLERANCIA_DIVERGENCIA, ordenado pelo maior impacto em quilos primeiro.
        """
        success, rows = self.select_all(self.TABLE, "status", "active", order_by="name")
        if not success:
            return False, []

        result = []
        for row in rows:
            if row["weight_kg"] is None or row["stock_kg_erp"] is None:
                continue

            peso_teorico = float(row["stock_quantity"]) * float(row["weight_kg"])
            kg_erp = float(row["stock_kg_erp"])
            divergencia_kg = kg_erp - peso_teorico
            divergencia_pct = (divergencia_kg / kg_erp) if kg_erp else 0.0

            if abs(divergencia_pct) < self.TOLERANCIA_DIVERGENCIA:
                continue

            result.append({
                **row,
                "peso_teorico_kg": round(peso_teorico, 3),
                "divergencia_kg": round(divergencia_kg, 3),
                "divergencia_pct": round(divergencia_pct * 100, 1),
            })

        result.sort(key=lambda item: abs(item["divergencia_kg"]), reverse=True)
        return True, result
