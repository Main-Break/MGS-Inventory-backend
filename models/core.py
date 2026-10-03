"""Cria/confere as tabelas do banco.

migrate() roda sozinho toda vez que o app sobe (ver main.py): confere o que
já existe e cria o que falta, sem precisar de nenhum passo manual no
servidor. Este arquivo é o schema completo e atual do banco - nunca criar
um "update_2.sql" solto por fora, sempre atualizar as tabelas aqui.
"""

from models.database import Database


class Core(Database):
    def migrate(self) -> None:
        with self:
            self.execute(
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
            self.execute(
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
            self.execute(
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
