"""
Ponto de entrada do sistema. Para rodar, na raiz do projeto:

    python main.py
"""

import uvicorn

from core import API, config
from register import register_routes

register_routes(API)


if __name__ == "__main__":
    uvicorn.run(API, host=config.HOST, port=config.PORT)
