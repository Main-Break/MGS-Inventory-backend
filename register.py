"""
Registro das rotas na aplicação FastAPI.

Para adicionar uma seção nova na API, crie o arquivo em routes/ e acrescente
uma linha aqui. Nenhum outro arquivo precisa mudar.
"""

from fastapi import FastAPI

from routes import auth, itens, materials, users, verifications


def register_routes(api: FastAPI) -> None:
    api.include_router(auth.router)
    api.include_router(users.router)
    api.include_router(materials.router)
    api.include_router(itens.router)
    api.include_router(verifications.router)
