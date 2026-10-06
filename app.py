"""Ponto de entrada do sistema. Roda direto:

    python app.py
"""

import uvicorn

import config
from main import app
from routes_register import register_routes

register_routes(app)


if __name__ == "__main__":
    uvicorn.run("app:app", host=config.HOST, port=config.PORT, reload=True)
