"""
Ponto de entrada do sistema. Para rodar, na raiz do projeto:

    python3 main.py

Não precisa ativar o .venv nem instalar nada à mão antes: se o Python que
chamou este arquivo não tiver as dependências do projeto (esqueceu de
ativar o .venv, ou o terminal está com um "python3" cacheado errado), este
arquivo prepara (criando se faltar) o .venv do projeto e se re-executa
sozinho com o interpretador de dentro dele, antes de importar qualquer
coisa do sistema. Rodando onde as dependências já estão instaladas
globalmente (ex: dentro do container Docker), isso não faz nada a mais.
"""

import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VENV_PYTHON = BASE_DIR / ".venv" / "bin" / "python3"


def _tem_as_dependencias(python: str) -> bool:
    return subprocess.run([python, "-c", "import fastapi, uvicorn"], capture_output=True).returncode == 0


def _instalar_dependencias() -> None:
    linhas = (BASE_DIR / "requirements.txt").read_text().splitlines()
    # ultralytics é pesado (traz o PyTorch) e não é preciso para subir o sistema:
    # sem modelo treinado, /verifications já responde 503 de qualquer jeito.
    pacotes = [linha.strip() for linha in linhas if linha.strip() and not linha.strip().startswith("#") and "ultralytics" not in linha]
    subprocess.run([str(VENV_PYTHON), "-m", "pip", "install", "--quiet", *pacotes], check=True)


def _preparar_e_reexecutar() -> None:
    print("Dependências não encontradas no Python atual, preparando .venv/ do projeto...")

    if not VENV_PYTHON.exists():
        subprocess.run([sys.executable, "-m", "venv", str(BASE_DIR / ".venv")], check=True)

    if not _tem_as_dependencias(str(VENV_PYTHON)):
        _instalar_dependencias()

    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]])


if not _tem_as_dependencias(sys.executable):
    _preparar_e_reexecutar()

import uvicorn

from core import API, config
from register import register_routes

if __name__ == "__main__":
    register_routes(API)
    uvicorn.run(API, host=config.HOST, port=config.PORT)
