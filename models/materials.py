"""
Operações da tabela materials (materiais de que os itens são feitos).

A densidade (peso específico em g/cm³) de cada material é usada nas equações
de peso e quantidade dos itens.

Não existe SQL aqui: tudo passa pelas funções da classe mãe Database.

Toda função devolve (sucesso, dado): em caso de sucesso, dado é o registro
(dicionário) ou a lista; em caso de falha, dado é uma mensagem pronta para
mostrar ao usuário.
"""

from database.database import Database


class DataMaterial(Database):

    TABLE = "materials"

    def find_by_id(self, material_id: str) -> tuple[bool, dict | str]:
        success, material = self.select_one(self.TABLE, "id", material_id)

        if not success or material is None:
            return False, "Material não encontrado."
        return True, material

    def find_by_code(self, code: str) -> tuple[bool, dict | str]:
        success, material = self.select_one(self.TABLE, "code", code.upper())

        if not success or material is None:
            return False, "Material não encontrado."
        return True, material

    def create(self, data: dict) -> tuple[bool, dict | str]:
        """
        Cadastra um material. data é um dicionário coluna -> valor, já validado pelo
        MaterialData de models/schemas.py.
        """
        # A sigla é guardada sempre em maiúsculo, assim "pead" e "PEAD" são o mesmo material.
        data = {**data, "code": data["code"].upper()}

        exists, _ = self.find_by_code(data["code"])
        if exists:
            return False, "Já existe um material com essa sigla."

        success, new_id = self.insert_table(self.TABLE, list(data.keys()), list(data.values()))

        if not success:
            return False, "Não foi possível cadastrar o material."
        return self.find_by_id(new_id)

    def update(self, material_id: str, data: dict) -> tuple[bool, dict | str]:
        exists, message = self.find_by_id(material_id)
        if not exists:
            return False, message

        data = {**data, "code": data["code"].upper()}

        # A nova sigla não pode pertencer a outro material.
        exists, other = self.find_by_code(data["code"])
        if exists and other["id"] != material_id:
            return False, "Já existe um material com essa sigla."

        success, _ = self.update_table(self.TABLE, list(data.keys()), list(data.values()), "id", material_id)

        if not success:
            return False, "Não foi possível atualizar o material."
        return self.find_by_id(material_id)

    def set_status(self, material_id: str, status: str) -> tuple[bool, dict | str]:
        """Muda o status: 'active', 'disable' ou 'deleted' (soft delete)."""
        exists, message = self.find_by_id(material_id)
        if not exists:
            return False, message

        self.update_table(self.TABLE, ["status"], [status], "id", material_id)
        return self.find_by_id(material_id)

    def list_all(self) -> tuple[bool, list]:
        return self.select_all(self.TABLE, order_by="code")

    def search(self, term: str | None = None) -> tuple[bool, list]:
        if not term:
            return self.list_all()
        return self.search_data(self.TABLE, ["code", "name"], term, order_by="code")
