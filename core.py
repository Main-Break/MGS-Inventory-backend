"""O inicial do projeto: variáveis de ambiente, pastas e conexão com o banco.

Tudo que as rotas e o cli.py precisam pra funcionar (config, banco, paths)
vem daqui. Todo SQL do projeto usa parâmetro (?), nunca concatena valor no
texto - é isso que protege contra SQL injection.
"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
NEURAL_DIR = BASE_DIR / "neural"
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads")))
TRAIN_DIR = UPLOAD_DIR / "train"

DB_FILE = os.getenv("DB_FILE", str(DATA_DIR / "database.db"))
MODEL_PATH = os.getenv("MODEL_PATH", str(NEURAL_DIR / "producao.pt"))
JWT_SECRET = os.getenv("JWT_SECRET", "troque-esta-chave-no-.env")

ADMIN_NAME = os.getenv("ADMIN_NAME", "Administrador")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@exemplo.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))


# --- Banco de dados (SQLite direto, sem ORM) ---


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
    Path(DB_FILE).parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(DB_FILE)
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
