"""O inicial do projeto: variáveis de ambiente e pastas.

Tudo que as rotas, o cli.py e os models precisam pra funcionar (config,
caminhos) vem daqui. O acesso ao banco em si fica nos models (models/).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
NEURAL_DIR = BASE_DIR / "neural"
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads")))
TRAIN_DIR = UPLOAD_DIR / "train"

DB_FILE = os.getenv("DB_FILE", str(DATA_DIR / "database.db"))
MODEL_PATH = os.getenv("MODEL_PATH", str(NEURAL_DIR / "producao.pt"))
JWT_SECRET = os.getenv("JWT_SECRET", "troque-esta-chave-no-.env")

ADMIN_NAME = os.getenv("ADMIN_NAME", "Administrador")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@exemplo.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
