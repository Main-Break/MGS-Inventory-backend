"""Operações da tabela verifications.

Toda função que busca/grava dado devolve (sucesso: bool, dado): em caso de
sucesso, dado é o registro (dict) ou lista; em caso de falha, dado é uma
mensagem pronta pra mostrar pro usuário/cliente da API.
"""

from models.database import Database


class DataVerification(Database):

    def create(
        self, user_id: int, item_id: int | None, photo_filename: str, detections_json: str
    ) -> tuple[bool, dict]:
        with self:
            new_id = self.execute(
                "INSERT INTO verifications (user_id, item_id, photo_filename, detections) VALUES (?, ?, ?, ?)",
                (user_id, item_id, photo_filename, detections_json),
            )
            return True, self.query_one("SELECT * FROM verifications WHERE id = ?", (new_id,))

    def find_by_id(self, verification_id: int) -> tuple[bool, dict | str]:
        with self:
            verification = self.query_one("SELECT * FROM verifications WHERE id = ?", (verification_id,))

        if verification is None:
            return False, "Verificação não encontrada."
        return True, verification

    def list_all(self) -> tuple[bool, list[dict]]:
        with self:
            return True, self.query_all("SELECT * FROM verifications ORDER BY id DESC")

    def list_by_user(self, user_id: int) -> tuple[bool, list[dict]]:
        with self:
            return True, self.query_all(
                "SELECT * FROM verifications WHERE user_id = ? ORDER BY id DESC", (user_id,)
            )

    def approve(self, verification_id: int, approved: bool) -> tuple[bool, dict | str]:
        with self:
            if self.query_one("SELECT id FROM verifications WHERE id = ?", (verification_id,)) is None:
                return False, "Verificação não encontrada."

            self.execute("UPDATE verifications SET approved = ? WHERE id = ?", (approved, verification_id))
            return True, self.query_one("SELECT * FROM verifications WHERE id = ?", (verification_id,))
