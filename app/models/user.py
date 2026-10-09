"""Operações da tabela users.

Toda função que busca/grava dado devolve (sucesso: bool, dado): em caso de
sucesso, dado é o registro (dict) ou lista; em caso de falha, dado é uma
mensagem pronta pra mostrar pro usuário/cliente da API.
"""

from app.models.database import Database


class DataUser(Database):

    def create(
        self, name: str, email: str, password_hash: str, role: str = "funcionario"
    ) -> tuple[bool, dict | str]:
        with self:
            if self.query_one("SELECT id FROM users WHERE email = ?", (email,)):
                return False, "Já existe um usuário com esse e-mail."

            new_id = self.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                (name, email, password_hash, role),
            )
            return True, self.query_one("SELECT * FROM users WHERE id = ?", (new_id,))

    def find_by_email(self, email: str) -> tuple[bool, dict | str]:
        with self:
            user = self.query_one("SELECT * FROM users WHERE email = ?", (email,))

        if user is None:
            return False, "Usuário não encontrado."
        return True, user

    def find_by_id(self, user_id: int) -> tuple[bool, dict | str]:
        with self:
            user = self.query_one("SELECT * FROM users WHERE id = ?", (user_id,))

        if user is None:
            return False, "Usuário não encontrado."
        return True, user

    def list_all(self) -> tuple[bool, list[dict]]:
        with self:
            return True, self.query_all("SELECT * FROM users ORDER BY id")

    def search(self, term: str | None = None) -> tuple[bool, list[dict]]:
        with self:
            if term:
                resultado = self.query_all(
                    "SELECT * FROM users WHERE name LIKE ? OR email LIKE ? ORDER BY id",
                    (f"%{term}%", f"%{term}%"),
                )
            else:
                resultado = self.query_all("SELECT * FROM users ORDER BY id")

        return True, resultado

    def update(self, user_id: int, name: str, email: str, password_hash: str) -> tuple[bool, dict]:
        with self:
            self.execute(
                "UPDATE users SET name = ?, email = ?, password_hash = ? WHERE id = ?",
                (name, email, password_hash, user_id),
            )
            return True, self.query_one("SELECT * FROM users WHERE id = ?", (user_id,))

    def set_active(self, user_id: int, active: bool) -> tuple[bool, dict | str]:
        with self:
            if self.query_one("SELECT id FROM users WHERE id = ?", (user_id,)) is None:
                return False, "Usuário não encontrado."

            self.execute("UPDATE users SET active = ? WHERE id = ?", (active, user_id))
            return True, self.query_one("SELECT * FROM users WHERE id = ?", (user_id,))

    def set_role(self, user_id: int, role: str) -> tuple[bool, dict | str]:
        with self:
            if self.query_one("SELECT id FROM users WHERE id = ?", (user_id,)) is None:
                return False, "Usuário não encontrado."

            self.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
            return True, self.query_one("SELECT * FROM users WHERE id = ?", (user_id,))

    def has_manager(self) -> bool:
        with self:
            return self.query_one("SELECT id FROM users WHERE role = 'gestor'") is not None
