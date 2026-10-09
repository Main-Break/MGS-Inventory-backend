"""API de inventário por foto: usuário fotografa, o modelo de IA conta os
itens, e fica registrado quem contou o quê.

Monta a instância do FastAPI: CORS, migração automática do banco e o
gestor inicial. As rotas em si não são penduradas aqui, e sim por
routes_register.py (chamado em app.py) - crescer o projeto com um domínio
novo (ex: fornecedores, pedidos) é criar um routes/novo_modulo.py e somar
uma linha em routes_register.py, sem precisar tocar neste arquivo.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from app.models.schema import DataSchema
from app.util.security import create_initial_manager


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
PORT = int(os.getenv("PORT", "5173"))

# Origem do front, pra liberar no CORS. Em dev é o endereço do Vite.
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

@asynccontextmanager
async def lifespan(_app: FastAPI):
    DataSchema(config.DB_FILE).migrate()
    create_initial_manager()
    yield


app = FastAPI(title="Inventário por Foto - API", lifespan=lifespan)

# Libera o front (outra origem, ex: localhost:5173) pra chamar a API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}