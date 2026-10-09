"""Conexão com o SQLite e criação das tabelas.

Todo SQL do projeto usa parâmetro (?), nunca concatena valor no texto -
é isso que protege contra SQL injection.
"""

import sqlite3
from contextlib import contextmanager

import core


class Banco:
    def __init__(self, conexao):
        self._conexao = conexao

    def buscar_um(self, sql, parametros=()):
        linhas = self.buscar_todos(sql, parametros)
        return linhas[0] if linhas else None

    def buscar_todos(self, sql, parametros=()):
        cursor = self._conexao.execute(sql, parametros)
        return [dict(linha) for linha in cursor.fetchall()]

    def executar(self, sql, parametros=()):
        return self._conexao.execute(sql, parametros).lastrowid


@contextmanager
def banco():
    conexao = sqlite3.connect(core.DB_FILE)
    conexao.row_factory = sqlite3.Row
    try:
        db = Banco(conexao)
        yield db
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def criar_tabelas() -> None:
    """Roda sozinho toda vez que o App sobe: cria o que ainda não existe."""
    with banco() as db:
        db.executar(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'funcionario',
                active INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        # label = nome exato da classe que o modelo de IA devolve.
        db.executar(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                stock_quantity INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        # detections guarda o resultado da IA (lista de label/count/confidence) como JSON.
        db.executar(
            """
            CREATE TABLE IF NOT EXISTS verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                item_id INTEGER REFERENCES items(id),
                photo_filename TEXT NOT NULL,
                detections TEXT NOT NULL,
                approved INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
