"""
Instancia do projeto FastAPI, com configuração de CORS e rota de saúde.
"""

# Imports
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models.schema import DataSchema
from app.util.security import create_initial_manager
from app.config import Config

# Carrega as configurações do projeto a partir do arquivo .env
config = Config()

# Define o lifespan da aplicação, que é executado no startup e shutdown.
@asynccontextmanager
async def lifespan(_app: FastAPI):
    DataSchema(config.DB_FILE).migrate()
    create_initial_manager()
    yield

# Instancia a aplicação FastAPI, com título, descrição e versão.
API = FastAPI(
    title="Inventário por Foto - API", 
    lifespan=lifespan,
    description="API para inventário por foto: usuário fotografa, o modelo de IA conta os itens, e fica registrado quem contou o quê.",
    version=config.VERSION,
)

# Libera o front (outra origem, ex: localhost:5173) pra chamar a API.
API.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rota de saúde da API, pra monitoramento.
@API.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}