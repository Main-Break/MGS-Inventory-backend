"""Ponto de entrada da API.

Sobe o FastAPI, aplica as migrações do banco antes de atender qualquer
requisição e registra as rotas.
"""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

import config
import migrations
from routes import auth, itens, users, verificacoes


@asynccontextmanager
async def ciclo_de_vida(_app: FastAPI):
    # As tabelas são criadas e atualizadas sozinhas toda vez que o App sobe,
    # então não existe passo manual de migração no servidor.
    migrations.aplicar_migracoes()
    migrations.criar_gestor_inicial()
    yield


app = FastAPI(title="Inventário por Foto - API", debug=config.DEBUG, lifespan=ciclo_de_vida)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(itens.router)
app.include_router(verificacoes.router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.RELOAD,
    )
