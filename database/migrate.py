"""
Migração automática do banco de dados.

Antes deste arquivo, o esquema (database/database.sql) era aplicado à mão
(mariadb ... < database.sql), o que depende de alguém lembrar de rodar isso em
cada servidor novo.

apply_schema() resolve isso: é chamada sozinha na subida do sistema (ver o
lifespan em core.py) e cria o que estiver faltando. Como todo comando do
database.sql é "CREATE TABLE IF NOT EXISTS", rodar de novo em um banco que já
tem as tabelas não faz nada, então é seguro chamar em toda subida.

database/database.sql continua sendo a única fonte do esquema: qualquer tabela
ou coluna nova é acrescentada ali, nunca em um arquivo solto separado.
"""

from pathlib import Path

import mysql.connector

SCHEMA_FILE = Path(__file__).resolve().parent / "database.sql"


def apply_schema(host: str, port: int, user: str, password: str, database: str) -> None:
    """Conecta no banco e executa database.sql inteiro, criando o que faltar."""
    commands = _split_commands(SCHEMA_FILE.read_text(encoding="utf-8"))

    conn = mysql.connector.connect(host=host, port=port, user=user, password=password, database=database)
    try:
        cursor = conn.cursor()
        for command in commands:
            cursor.execute(command)
        conn.commit()
        cursor.close()
    finally:
        conn.close()


def _split_commands(sql: str) -> list[str]:
    """Separa o arquivo em comandos individuais (um por ';'), sem os comentários ('--')."""
    lines = [line for line in sql.splitlines() if not line.strip().startswith("--")]
    without_comments = "\n".join(lines)

    return [command.strip() for command in without_comments.split(";") if command.strip()]
