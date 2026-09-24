"""Configurações do projeto, lidas do arquivo .env (ver .env.example).

É só leitura de variável de ambiente com valor padrão, sem biblioteca de
configuração no meio: para saber de onde sai qualquer ajuste, basta olhar
este arquivo.
"""

import os
import secrets

from dotenv import load_dotenv

load_dotenv()


def _texto(nome: str, padrao: str = "") -> str:
    return os.getenv(nome, padrao).strip()


def _numero(nome: str, padrao: int) -> int:
    valor = _texto(nome)
    return int(valor) if valor else padrao


def _booleano(nome: str, padrao: bool) -> bool:
    valor = _texto(nome).lower()
    if not valor:
        return padrao
    return valor in ("1", "true", "sim", "yes")


# Banco de dados: SQLITE (padrão, desenvolvimento) ou MYSQL / MARIADB.
DB_TYPE = _texto("DB_TYPE", "SQLITE").upper()
SQLITE_FILE = _texto("SQLITE_FILE", "./inventario.db")
DB_HOST = _texto("DB_HOST")
DB_PORT = _numero("DB_PORT", 3306)
DB_DATABASE = _texto("DB_DATABASE")
DB_USERNAME = _texto("DB_USERNAME")
DB_PASS = _texto("DB_PASS")

# Servidor
HOST = _texto("HOST", "0.0.0.0")
PORT = _numero("PORT", 8000)
RELOAD = _booleano("RELOAD", True)
DEBUG = _booleano("DEBUG", True)

# Autenticação (JWT)
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = _numero("JWT_EXPIRE_MINUTES", 480)  # 8h, um turno de trabalho
JWT_SECRET = _texto("JWT_SECRET")
if not JWT_SECRET:
    if not DEBUG:
        raise RuntimeError("Defina JWT_SECRET no .env para rodar em produção (DEBUG=false).")
    # Só em desenvolvimento: chave sorteada para esta execução, ou seja, os
    # tokens emitidos param de valer quando o processo reinicia.
    JWT_SECRET = secrets.token_urlsafe(32)

# Gestor criado automaticamente na primeira subida, se ainda não existir
# nenhum gestor no banco (sem isso ninguém consegue criar o primeiro usuário).
ADMIN_NAME = _texto("ADMIN_NAME", "Administrador")
ADMIN_EMAIL = _texto("ADMIN_EMAIL", "admin@exemplo.com").lower()
ADMIN_PASSWORD = _texto("ADMIN_PASSWORD")

# Fotos enviadas e modelo de detecção (.pt do YOLO).
UPLOAD_DIR = _texto("UPLOAD_DIR", "./uploads")
MAX_UPLOAD_SIZE_MB = _numero("MAX_UPLOAD_SIZE_MB", 15)
MODEL_PATH = _texto("MODEL_PATH", "./modelos/producao.pt")
