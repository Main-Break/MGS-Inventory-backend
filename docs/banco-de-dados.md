# Banco de dados

Banco relacional: MySQL ou MariaDB. Sem ORM, o SQL fica todo em
`database/database.py` (ver `docs/arquitetura.md`).

## Esquema

`database/database.sql` é a fonte única e consolidada do esquema. Reflete
sempre o estado atual de todas as tabelas, nunca existe um arquivo solto de
incremento (tipo `update_2.sql`). Toda alteração de tabela é feita direto
nesse arquivo.

Tabelas: `users`, `user_permissions`, `materials`, `itens`, `verifications`.
A descrição de cada coluna está comentada no próprio `database.sql`.

Padrões usados em todas as tabelas:

- `id`: `CHAR(36)`, um UUID-4 gerado pela classe `Database` no `insert`
  (`database/database.py::insert_table`). Ninguém adivinha o id de outro
  registro.
- `status`: `active`, `disable` ou `deleted`. Para "apagar" um registro, o
  status vira `deleted` (soft delete), assim o histórico de verificações
  continua íntegro mesmo se o item ou usuário envolvido for removido.
- `created_at` / `updated_at`: preenchidos e atualizados pelo próprio banco
  (`DEFAULT CURRENT_TIMESTAMP` / `ON UPDATE CURRENT_TIMESTAMP`).

## Migração automática

Antes de existir `database/migrate.py`, o esquema era aplicado à mão
(`mariadb -u USUARIO -p BANCO < database/database.sql`) em cada servidor.
Isso já causou incidente real em outros projetos: alguém esquece de rodar o
arquivo e a tabela ou coluna nova simplesmente não existe em produção.

Agora, `core.py` chama `apply_schema()` (de `database/migrate.py`) no
`lifespan` da aplicação, ou seja, toda vez que o sistema sobe. A função lê
`database/database.sql` inteiro e executa cada comando. Como todo `CREATE
TABLE` é `IF NOT EXISTS`, rodar de novo num banco que já tem as tabelas não
faz nada, então é seguro chamar sempre, sem precisar verificar se é a
primeira vez.

Se uma tabela ganhar uma coluna nova no futuro, o `CREATE TABLE IF NOT
EXISTS` não altera uma tabela já existente. Nesse caso, quem alterar
`database.sql` deve acrescentar um `ALTER TABLE ... ADD COLUMN IF NOT
EXISTS` correspondente no mesmo arquivo (o MariaDB recente aceita essa
sintaxe), para que `apply_schema()` continue sem exigir passo manual. Até a
entrega deste MVP, nenhuma mudança incremental desse tipo foi necessária.

## Como rodar localmente

```bash
# cria o usuário e os dois bancos (uso normal e testes), uma vez só:
sudo mariadb -e "
CREATE USER IF NOT EXISTS 'inventario'@'localhost' IDENTIFIED BY 'sua-senha';
CREATE DATABASE IF NOT EXISTS inventario CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS inventario_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON inventario.* TO 'inventario'@'localhost';
GRANT ALL PRIVILEGES ON inventario_test.* TO 'inventario'@'localhost';
FLUSH PRIVILEGES;
"

cp .env.example .env   # preencha DB_*, DB_NAME_TEST, JWT_SECRET e ADMIN_*
python main.py         # o esquema é criado sozinho na subida
```

Nenhum passo manual de `mariadb ... < database.sql` é mais necessário.

## Backup

`data/backup/` é a pasta prevista para backups (`.sql` ou dump do banco).
Gerar o backup em si (ex: `mariadb-dump`) ainda não está automatizado, fica
como ponto de atenção para quem assumir o projeto (ver
`docs/pendencias.md`).
