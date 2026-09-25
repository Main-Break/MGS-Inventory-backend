"""Configurações lidas do .env."""

import os

from dotenv import load_dotenv

load_dotenv()

DB_FILE = os.getenv("DB_FILE", "inventario.db")
JWT_SECRET = os.getenv("JWT_SECRET", "troque-esta-chave-no-.env")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MODEL_PATH = os.getenv("MODEL_PATH", "modelos/producao.pt")

ADMIN_NAME = os.getenv("ADMIN_NAME", "Administrador")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@exemplo.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
