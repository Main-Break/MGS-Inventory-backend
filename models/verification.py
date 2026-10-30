"""
Operações da tabela verifications (fotos conferidas pela IA).

Não existe SQL aqui: tudo passa pelas funções da classe mãe Database.

Toda função devolve (sucesso, dado): em caso de sucesso, dado é o registro
(dicionário) ou a lista; em caso de falha, dado é uma mensagem pronta para
mostrar ao usuário.
"""

from database.database import Database


class DataVerification(Database):

    TABLE = "verifications"

    def find_by_id(self, verification_id: str) -> tuple[bool, dict | str]:
        success, verification = self.select_one(self.TABLE, "id", verification_id)

        if not success or verification is None:
            return False, "Verificação não encontrada."
        return True, verification

    def create(self, user_id: str, item_id: str | None, photo_filename: str, detections_json: str) -> tuple[bool, dict | str]:
        success, new_id = self.insert_table(
            self.TABLE,
            ["user_id", "item_id", "photo_filename", "detections"],
            [user_id, item_id, photo_filename, detections_json]
        )

        if not success:
            return False, "Não foi possível salvar a verificação."
        return self.find_by_id(new_id)

    def list_all(self) -> tuple[bool, list]:
        return self.select_all(self.TABLE, order_by="created_at", descending=True)

    def list_by_user(self, user_id: str) -> tuple[bool, list]:
        return self.select_all(self.TABLE, "user_id", user_id, order_by="created_at", descending=True)

    def approve(self, verification_id: str, approved: bool) -> tuple[bool, dict | str]:
        exists, message = self.find_by_id(verification_id)
        if not exists:
            return False, message

        self.update_table(self.TABLE, ["approved"], [approved], "id", verification_id)
        return self.find_by_id(verification_id)
