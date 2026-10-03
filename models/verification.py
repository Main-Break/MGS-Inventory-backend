"""Operações da tabela verifications."""

from models.database import Database


class Verification(Database):
    def create(self, user_id: int, item_id: int | None, photo_filename: str, detections_json: str) -> dict:
        with self:
            new_id = self.execute(
                "INSERT INTO verifications (user_id, item_id, photo_filename, detections) VALUES (?, ?, ?, ?)",
                (user_id, item_id, photo_filename, detections_json),
            )
            return self.query_one("SELECT * FROM verifications WHERE id = ?", (new_id,))

    def find_by_id(self, verification_id: int) -> dict | None:
        with self:
            return self.query_one("SELECT * FROM verifications WHERE id = ?", (verification_id,))

    def list_all(self) -> list[dict]:
        with self:
            return self.query_all("SELECT * FROM verifications ORDER BY id DESC")

    def list_by_user(self, user_id: int) -> list[dict]:
        with self:
            return self.query_all(
                "SELECT * FROM verifications WHERE user_id = ? ORDER BY id DESC", (user_id,)
            )

    def approve(self, verification_id: int, approved: bool) -> dict | None:
        with self:
            if self.query_one("SELECT id FROM verifications WHERE id = ?", (verification_id,)) is None:
                return None
            self.execute("UPDATE verifications SET approved = ? WHERE id = ?", (approved, verification_id))
            return self.query_one("SELECT * FROM verifications WHERE id = ?", (verification_id,))
