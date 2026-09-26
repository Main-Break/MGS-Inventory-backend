"""API de inventário por foto: usuário fotografa, o modelo de IA conta os
itens, e fica registrado quem contou o quê.

Junta as rotas de cada seção (routes/) num app só e sobe o servidor.
"""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

import core
from routes import auth, items, users, verifications
from security import criar_gestor_inicial


@asynccontextmanager
async def ciclo_de_vida(_app: FastAPI):
    core.criar_tabelas()
    criar_gestor_inicial()
    yield


app = FastAPI(title="Inventário por Foto - API", lifespan=ciclo_de_vida)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(items.router)
app.include_router(verifications.router)


if __name__ == "__main__":
    uvicorn.run("main:app", host=core.HOST, port=core.PORT, reload=True)
