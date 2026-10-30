"""
Operações da tabela user_permissions (permissões extras de cada usuário).

Como funciona:
    - O gestor sempre pode tudo, não precisa de permissão cadastrada.
    - O funcionário pode o básico (enviar fotos, ver as próprias verificações,
      consultar itens e materiais) e mais o que o gestor liberar para ele.

Para criar uma permissão nova, acrescente a chave em PERMISSIONS e use
require_permission("chave") na rota (ver core.py). A tabela não muda.

Não existe SQL aqui: tudo passa pelas funções da classe mãe Database.
"""

from database.database import Database


class DataPermission(Database):

    TABLE = "user_permissions"

    # Todas as permissões que podem ser liberadas, com a descrição mostrada ao gestor.
    PERMISSIONS = {
        "users.create": "Cadastrar usuários (somente funcionários)",
        "users.list": "Listar e buscar usuários",
        "users.status": "Ativar, desativar e apagar usuários (exceto gestores)",
        "materials.create": "Cadastrar materiais",
        "materials.edit": "Editar materiais",
        "materials.status": "Ativar, desativar e apagar materiais",
        "itens.create": "Cadastrar itens",
        "itens.edit": "Editar itens",
        "itens.status": "Ativar, desativar e apagar itens",
        "verifications.view_all": "Ver as verificações de todos os usuários",
        "verifications.approve": "Aprovar e reprovar verificações",
    }

    def list_by_user(self, user_id: str) -> tuple[bool, list]:
        """Devolve a lista de chaves liberadas para o usuário, ex: ["itens.create", "itens.edit"]."""
        success, rows = self.select_all(self.TABLE, "user_id", user_id, order_by="permission")
        return success, [row["permission"] for row in rows]

    def grant(self, user_id: str, permission: str) -> tuple[bool, list | str]:
        """Libera a permissão para o usuário e devolve a lista atualizada."""
        if permission not in self.PERMISSIONS:
            return False, f"Permissão inexistente: {permission}"

        _, granted = self.list_by_user(user_id)

        # Liberar o que já está liberado não é erro, só não faz nada.
        if permission not in granted:
            success, _ = self.insert_table(self.TABLE, ["user_id", "permission"], [user_id, permission])
            if not success:
                return False, "Não foi possível liberar a permissão."

        return self.list_by_user(user_id)

    def revoke(self, user_id: str, permission: str) -> tuple[bool, list | str]:
        """Retira a permissão do usuário e devolve a lista atualizada."""
        if permission not in self.PERMISSIONS:
            return False, f"Permissão inexistente: {permission}"

        # Procura o registro dessa permissão para apagar pelo id.
        _, rows = self.select_all(self.TABLE, "user_id", user_id)
        for row in rows:
            if row["permission"] == permission:
                self.delete_data(self.TABLE, "id", row["id"])

        return self.list_by_user(user_id)
