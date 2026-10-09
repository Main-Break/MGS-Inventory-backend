import os
from pathlib import Path
from dotenv import load_dotenv

class Config:
    """Configurações do projeto, carregadas do .env."""

    def __init__(self):
        load_dotenv()

        self.BASE_DIR = Path(__file__).resolve().parent
        self.DATA_DIR = self.BASE_DIR / "data"
        self.NEURAL_DIR = self.BASE_DIR / "neural"
        self.UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(self.BASE_DIR / "uploads")))
        self.TRAIN_DIR = self.UPLOAD_DIR / "train"

        self.VERSION = os.getenv("VERSION", "0.1.0")

        self.DB_FILE = os.getenv("DB_FILE", str(self.DATA_DIR / "database.db"))
        self.MODEL_PATH = os.getenv("MODEL_PATH", str(self.NEURAL_DIR / "producao.pt"))
        self.JWT_SECRET = os.getenv("JWT_SECRET", "troque-esta-chave-no-.env")

        self.ADMIN_NAME = os.getenv("ADMIN_NAME", "Administrador")
        self.ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@exemplo.com")
        self.ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.PORT = int(os.getenv("PORT", "5173"))

        # Origem do front, pra liberar no CORS. Em dev é o endereço do Vite.
        self.FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")