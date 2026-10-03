"""Operações da tabela users."""

from models.database import Database


class EmailAlreadyRegisteredError(Exception):
    pass


class User(Database):
    def create(self, name: str, email: str, password_hash: str, role: str = "funcionario") -> dict:
        with self:
            if self.query_one("SELECT id FROM users WHERE email = ?", (email,)):
                raise EmailAlreadyRegisteredError(email)
            new_id = self.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                (name, email, password_hash, role),
            )
            return self.query_one("SELECT * FROM users WHERE id = ?", (new_id,))

    def find_by_email(self, email: str) -> dict | None:
        with self:
            return self.query_one("SELECT * FROM users WHERE email = ?", (email,))

    def find_by_id(self, user_id: int) -> dict | None:
        with self:
            return self.query_one("SELECT * FROM users WHERE id = ?", (user_id,))

    def list_all(self) -> list[dict]:
        with self:
            return self.query_all("SELECT * FROM users ORDER BY id")

    def update(self, user_id: int, name: str, email: str, password_hash: str) -> dict:
        with self:
            self.execute(
                "UPDATE users SET name = ?, email = ?, password_hash = ? WHERE id = ?",
                (name, email, password_hash, user_id),
            )
            return self.query_one("SELECT * FROM users WHERE id = ?", (user_id,))

    def set_active(self, user_id: int, active: bool) -> dict | None:
        with self:
            if self.query_one("SELECT id FROM users WHERE id = ?", (user_id,)) is None:
                return None
            self.execute("UPDATE users SET active = ? WHERE id = ?", (active, user_id))
            return self.query_one("SELECT * FROM users WHERE id = ?", (user_id,))

    def has_manager(self) -> bool:
        with self:
            return self.query_one("SELECT id FROM users WHERE role = 'gestor'") is not None
