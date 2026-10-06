"""API de inventário por foto: usuário fotografa, o modelo de IA conta os
itens, e fica registrado quem contou o quê.

Monta a instância do FastAPI: CORS, migração automática do banco e o
gestor inicial. As rotas em si não são penduradas aqui, e sim por
routes_register.py (chamado em app.py) - crescer o projeto com um domínio
novo (ex: fornecedores, pedidos) é criar um routes/novo_modulo.py e somar
uma linha em routes_register.py, sem precisar tocar neste arquivo.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from models.schema import DataSchema
from security import create_initial_manager


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
