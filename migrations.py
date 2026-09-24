"""Migração automática do banco.

Roda sozinha toda vez que o App sobe (ver main.py), antes de atender
qualquer requisição: confere na tabela schema_migrations o que já foi
aplicado e executa o que estiver faltando. Não existe passo manual no
servidor, nem arquivo .sql solto para alguém lembrar de rodar.

Para mudar o schema depois: acrescente uma entrada nova em MIGRACOES com o
próximo número e o SQL, e atualize o database.sql (que é o schema completo
consolidado, só para consulta).
"""

import config
from database import USANDO_SQLITE, banco
from seguranca import gerar_hash_senha

# A sintaxe de id autoincremento muda entre SQLite e MySQL/MariaDB.
_ID = "INTEGER PRIMARY KEY AUTOINCREMENT" if USANDO_SQLITE else "INT AUTO_INCREMENT PRIMARY KEY"

MIGRACOES: list[tuple[int, str, list[str]]] = [
    (
        1,
        "cria usuarios, itens e verificacoes",
        [
            f"""
            CREATE TABLE users (
                id {_ID},
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL CHECK (role IN ('gestor', 'funcionario')),
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
            # Catálogo do estoque. O label é o nome exato da classe que o
            # modelo devolve (ex: "bastao_redondo_preto"); o funcionário
            # procura por name/label antes de fotografar.
            f"""
            CREATE TABLE items (
                id {_ID},
                label VARCHAR(100) NOT NULL UNIQUE,
                name VARCHAR(255) NOT NULL,
                stock_quantity INT NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
            # Uma verificação = uma contagem feita por alguém, com 1 ou mais
            # fotos. expected_item_id é o item que o funcionário selecionou
            # para contar; manual_count é a recontagem que ele mesmo informa
            # para comparar com a IA; approved é do gestor e fica nulo até
            # ele revisar (revisar é opcional).
            f"""
            CREATE TABLE verifications (
                id {_ID},
                user_id INT NOT NULL REFERENCES users(id),
                expected_item_id INT NULL REFERENCES items(id),
                manual_count INT NULL,
                approved BOOLEAN NULL,
                approved_by INT NULL REFERENCES users(id),
                approved_at DATETIME NULL,
                approval_note VARCHAR(500) NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
            f"""
            CREATE TABLE verification_photos (
                id {_ID},
                verification_id INT NOT NULL REFERENCES verifications(id),
                image_filename VARCHAR(255) NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
            # Uma linha por classe detectada na verificação, já somando o que
            # apareceu em todas as fotos dela. item_id fica nulo quando o
            # label detectado não bate com nenhum item cadastrado.
            f"""
            CREATE TABLE verification_items (
                id {_ID},
                verification_id INT NOT NULL REFERENCES verifications(id),
                item_id INT NULL REFERENCES items(id),
                label VARCHAR(100) NOT NULL,
                count INT NOT NULL,
                avg_confidence FLOAT NOT NULL
            )
            """,
        ],
    ),
]


def aplicar_migracoes() -> None:
    with banco() as db:
        db.executar(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        aplicadas = {linha["version"] for linha in db.buscar_todos("SELECT version FROM schema_migrations")}

        for versao, nome, comandos in sorted(MIGRACOES):
            if versao in aplicadas:
                continue
            for comando in comandos:
                db.executar(comando)
            db.executar(
                "INSERT INTO schema_migrations (version, name) VALUES (:version, :name)",
                {"version": versao, "name": nome},
            )
            print(f"migração {versao} aplicada: {nome}")


def criar_gestor_inicial() -> None:
    """Garante que sempre exista pelo menos um gestor. Só gestor cria
    usuário, então sem isso o sistema subiria sem ninguém para entrar."""
    with banco() as db:
        if db.buscar_um("SELECT id FROM users WHERE role = 'gestor' LIMIT 1") is not None:
            return

        if not config.ADMIN_PASSWORD:
            raise RuntimeError(
                "Não existe nenhum gestor cadastrado e ADMIN_PASSWORD não foi definido no .env. "
                "Defina ADMIN_PASSWORD (e se quiser ADMIN_EMAIL) para criar o gestor inicial."
            )

        db.executar(
            """
            INSERT INTO users (name, email, password_hash, role, active)
            VALUES (:name, :email, :password_hash, 'gestor', TRUE)
            """,
            {
                "name": config.ADMIN_NAME,
                "email": config.ADMIN_EMAIL,
                "password_hash": gerar_hash_senha(config.ADMIN_PASSWORD),
            },
        )
        print(f"gestor inicial criado: {config.ADMIN_EMAIL}")
