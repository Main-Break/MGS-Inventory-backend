"""Ponto de entrada do sistema. Roda direto:

    python app.py
"""

import uvicorn
import config
from app.app import app, HOST, PORT
from app.routes_register import register_routes

register_routes(app)


"""O inicial do projeto: variáveis de ambiente e pastas.

Tudo que as rotas, o cli.py e os models precisam pra funcionar (config,
caminhos) vem daqui. O acesso ao banco em si fica nos models (models/).
"""

if __name__ == "__main__":
    uvicorn.run("app:app", host=HOST, port=PORT, reload=True)