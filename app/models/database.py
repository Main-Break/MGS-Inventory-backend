"""Classe base de acesso ao banco: conexão e execução direta de SQL.

Todo SQL daqui pra baixo usa `?` para valores, nunca concatena texto do
usuário na query - é isso que protege contra SQL injection. Nomes de tabela
e coluna são sempre fixos no código de cada model, nunca vêm de fora.
"""

import sqlite3
from pathlib import Path


class Database:
    def __init__(self, database_file: str = "database.db") -> None:
        self._file = database_file
        self._conn: sqlite3.Connection | None = None

    def __enter__(self) -> "Database":
        Path(self._file).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._file)
        self._conn.row_factory = sqlite3.Row
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is None:
            self._conn.commit()
        else:
            self._conn.rollback()
        self._conn.close()
        self._conn = None

    def query_one(self, sql: str, params: tuple = ()) -> dict | None:
        linha = self._conn.execute(sql, params).fetchone()
        return dict(linha) if linha else None

    def query_all(self, sql: str, params: tuple = ()) -> list[dict]:
        linhas = self._conn.execute(sql, params).fetchall()
        return [dict(linha) for linha in linhas]

    def execute(self, sql: str, params: tuple = ()) -> int:
        return self._conn.execute(sql, params).lastrowid
