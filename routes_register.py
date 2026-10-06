"""Pendura cada módulo de routes/ na instância do FastAPI (ver main.py).

Ponto único de registro de rotas: crescer o projeto com um domínio novo
significa criar um routes/novo_modulo.py e somar uma linha aqui - main.py
não precisa mudar.
"""

from fastapi import FastAPI

from routes import auth, items, users, verifications


def register_routes(app: FastAPI) -> None:
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(items.router)
    app.include_router(verifications.router)
