"""Acesso ao banco de dados, sem ORM.

Todo SQL do sistema fica escrito à mão dentro das rotas, sempre com
parâmetros nomeados (:nome). Os valores nunca são colados no texto do SQL,
quem os substitui é o driver do banco, e é isso que fecha a porta para SQL
injection.

Funciona em SQLite (padrão, desenvolvimento) e em MySQL/MariaDB (produção).
"""

import re
import sqlite3
from contextlib import contextmanager
from typing import Any

import config

USANDO_SQLITE = config.DB_TYPE == "SQLITE"

# O SQL do projeto é escrito no formato do SQLite (:nome). O driver do MySQL
# usa outro formato para a mesma coisa (%(nome)s), então a tradução acontece
# aqui, num lugar só, sem mudar em nada a segurança: continua sendo parâmetro.
_PARAMETRO = re.compile(r":([a-zA-Z_][a-zA-Z0-9_]*)")


def _abrir_conexao():
    if USANDO_SQLITE:
        conexao = sqlite3.connect(config.SQLITE_FILE)
        conexao.row_factory = sqlite3.Row
        # O SQLite ignora as FOREIGN KEY se isso não for ligado a cada conexão.
        conexao.execute("PRAGMA foreign_keys = ON")
        return conexao

    if not config.DB_HOST or not config.DB_DATABASE or not config.DB_USERNAME:
        raise RuntimeError(
            f"DB_TYPE={config.DB_TYPE} exige DB_HOST, DB_DATABASE e DB_USERNAME preenchidos no .env"
        )

    # MariaDB fala o mesmo protocolo do MySQL, então usa o mesmo driver.
    import pymysql

    return pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USERNAME,
        password=config.DB_PASS,
        database=config.DB_DATABASE,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


class Banco:
    """Três operações, que é tudo que as rotas precisam: buscar uma linha,
    buscar várias, e executar um INSERT/UPDATE/DELETE."""

    def __init__(self, conexao) -> None:
        self._conexao = conexao

    def buscar_um(self, sql: str, parametros: dict[str, Any] | None = None) -> dict | None:
        linhas = self.buscar_todos(sql, parametros)
        return linhas[0] if linhas else None

    def buscar_todos(self, sql: str, parametros: dict[str, Any] | None = None) -> list[dict]:
        cursor = self._executar(sql, parametros)
        linhas = [dict(linha) for linha in cursor.fetchall()]
        cursor.close()
        return linhas

    def executar(self, sql: str, parametros: dict[str, Any] | None = None) -> int:
        """Devolve o id gerado (útil depois de um INSERT)."""
        cursor = self._executar(sql, parametros)
        id_gerado = cursor.lastrowid
        cursor.close()
        return id_gerado

    def _executar(self, sql: str, parametros: dict[str, Any] | None):
        cursor = self._conexao.cursor()
        cursor.execute(sql if USANDO_SQLITE else _PARAMETRO.sub(r"%(\1)s", sql), parametros or {})
        return cursor


@contextmanager
def banco():
    """Abre uma conexão, dá commit no fim do bloco e rollback se estourar erro:

        with banco() as db:
            usuario = db.buscar_um("SELECT ...", {"id": 1})
    """
    conexao = _abrir_conexao()
    try:
        db = Banco(conexao)
        yield db
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()
