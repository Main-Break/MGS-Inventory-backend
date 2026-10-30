"""
Registro das rotas na aplicação FastAPI.

Duas famílias de rotas:
    - routes/  a API JSON, para outros sistemas (ERPs) consumirem.
    - views/   a interface web (HTML), prefixo "/app", para uso humano.

Para adicionar uma seção nova em qualquer uma das duas, crie o arquivo na
pasta certa e acrescente uma linha aqui. Nenhum outro arquivo precisa mudar.
"""

from fastapi import FastAPI

from routes import auth, itens, materials, users, verifications
from views import auth as web_auth, dashboard, itens as web_itens, materials as web_materials, users as web_users, verifications as web_verifications


def register_routes(api: FastAPI) -> None:
    # API JSON.
    api.include_router(auth.router)
    api.include_router(users.router)
    api.include_router(materials.router)
    api.include_router(itens.router)
    api.include_router(verifications.router)

    # Interface web.
    api.include_router(web_auth.router)
    api.include_router(dashboard.router)
    api.include_router(web_users.router)
    api.include_router(web_materials.router)
    api.include_router(web_itens.router)
    api.include_router(web_verifications.router)
