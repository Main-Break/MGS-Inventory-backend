"""
Operações da tabela users.

Não existe SQL aqui: tudo passa pelas funções da classe mãe Database.

Toda função devolve (sucesso, dado): em caso de sucesso, dado é o registro
(dicionário) ou a lista; em caso de falha, dado é uma mensagem pronta para
mostrar ao usuário.
"""

from database.database import Database


class DataUser(Database):

    TABLE = "users"

    def find_by_id(self, user_id: str) -> tuple[bool, dict | str]:
        success, user = self.select_one(self.TABLE, "id", user_id)

        if not success or user is None:
            return False, "Usuário não encontrado."
        return True, user

    def find_by_email(self, email: str) -> tuple[bool, dict | str]:
        success, user = self.select_one(self.TABLE, "email", email)

        if not success or user is None:
            return False, "Usuário não encontrado."
        return True, user

    def create(self, name: str, email: str, password_hash: str, role: str = "funcionario") -> tuple[bool, dict | str]:
        # O e-mail é usado no login, então não pode repetir.
        exists, _ = self.find_by_email(email)
        if exists:
            return False, "Já existe um usuário com esse e-mail."

        success, new_id = self.insert_table(
            self.TABLE,
            ["name", "email", "password_hash", "role"],
            [name, email, password_hash, role]
        )

        if not success:
            return False, "Não foi possível cadastrar o usuário."
        return self.find_by_id(new_id)

    def list_all(self) -> tuple[bool, list]:
        return self.select_all(self.TABLE, order_by="name")

    def search(self, term: str | None = None) -> tuple[bool, list]:
        if not term:
            return self.list_all()
        return self.search_data(self.TABLE, ["name", "email"], term, order_by="name")

    def update(self, user_id: str, name: str, email: str, password_hash: str) -> tuple[bool, dict | str]:
        # O novo e-mail não pode pertencer a outro usuário.
        exists, other = self.find_by_email(email)
        if exists and other["id"] != user_id:
            return False, "Já existe um usuário com esse e-mail."

        success, _ = self.update_table(
            self.TABLE,
            ["name", "email", "password_hash"],
            [name, email, password_hash],
            "id", user_id
        )

        if not success:
            return False, "Não foi possível atualizar o usuário."
        return self.find_by_id(user_id)

    def set_status(self, user_id: str, status: str) -> tuple[bool, dict | str]:
        """Muda o status: 'active', 'disable' ou 'deleted' (soft delete)."""
        exists, message = self.find_by_id(user_id)
        if not exists:
            return False, message

        self.update_table(self.TABLE, ["status"], [status], "id", user_id)
        return self.find_by_id(user_id)

    def set_role(self, user_id: str, role: str) -> tuple[bool, dict | str]:
        """Muda a função: 'gestor' ou 'funcionario'."""
        exists, message = self.find_by_id(user_id)
        if not exists:
            return False, message

        self.update_table(self.TABLE, ["role"], [role], "id", user_id)
        return self.find_by_id(user_id)

    def has_manager(self) -> bool:
        success, manager = self.select_one(self.TABLE, "role", "gestor")
        return success and manager is not None
