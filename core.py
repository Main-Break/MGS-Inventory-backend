"""
Núcleo do projeto: configurações, objetos compartilhados e a aplicação FastAPI.

Ordem de dependência do projeto (cada parte só conhece as anteriores):

    database/  ->  models/  ->  core.py  ->  routes/  ->  register.py  ->  main.py

    - database/database.py  classe mãe Database, único lugar com SQL.
    - models/               uma classe por tabela, herdando de Database.
    - core.py               lê o .env, cria os objetos (models, rede neural) e o app.
    - routes/               rotas da API, usam os objetos criados aqui.
    - register.py           registra as rotas no app.
    - main.py               sobe o servidor.
"""

# Imports
import os
from pathlib import Path
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from models.user import DataUser
from models.itens import DataItem
from models.materials import DataMaterial
from models.permissions import DataPermission
from models.verification import DataVerification
from neural.neural import Neural
from util.security import hash_password, read_token


# ----------------------------------------------------------------------------
# Configurações
# ----------------------------------------------------------------------------
class Config:
    """Configurações do projeto, lidas do arquivo .env."""

    def __init__(self) -> None:
        load_dotenv()

        self.VERSION = os.getenv("VERSION", "0.1.0")

        # Pastas do projeto.
        self.BASE_DIR = Path(__file__).resolve().parent
        self.DATA_DIR = self.BASE_DIR / "data"
        self.TRAIN_DIR = self.DATA_DIR / "train"        # imagens e datasets de treinamento
        self.CACHE_DIR = self.DATA_DIR / "database"     # arquivos .db / .sqlite de cache
        self.BACKUP_DIR = self.DATA_DIR / "backup"      # backups do banco (.sql, .db)
        self.UPLOAD_DIR = self.DATA_DIR / "upload"      # fotos enviadas nas verificações
        self.NEURAL_DIR = self.BASE_DIR / "neural"

        # Banco de dados principal (MySQL / MariaDB).
        # Fica em um dicionário para ser passado direto aos models, ex: DataUser(**config.DATABASE)
        self.DATABASE = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "3306")),
            "user": os.getenv("DB_USER", ""),
            "password": os.getenv("DB_PASSWORD", ""),
            "database": os.getenv("DB_NAME", ""),
        }

        # Rede neural: modelo treinado usado nas verificações.
        self.MODEL_PATH = os.getenv("MODEL_PATH", str(self.NEURAL_DIR / "producao.pt"))

        # Segurança: chave usada para assinar os tokens de acesso.
        self.JWT_SECRET = os.getenv("JWT_SECRET", "troque-esta-chave-no-.env")

        # Gestor criado sozinho na primeira vez que o sistema sobe.
        self.ADMIN_NAME = os.getenv("ADMIN_NAME", "Administrador")
        self.ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@exemplo.com")
        self.ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

        # Servidor da API.
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.PORT = int(os.getenv("PORT", "8000"))

        # Endereço do front-end, liberado no CORS. Em desenvolvimento é o endereço do Vite.
        self.FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    def create_folders(self) -> None:
        """Cria as pastas de dados, caso ainda não existam."""
        for folder in [self.TRAIN_DIR, self.CACHE_DIR, self.BACKUP_DIR, self.UPLOAD_DIR]:
            folder.mkdir(parents=True, exist_ok=True)


config = Config()
config.create_folders()


# ----------------------------------------------------------------------------
# Objetos compartilhados pelo projeto inteiro (rotas e CLI)
# ----------------------------------------------------------------------------
users = DataUser(**config.DATABASE)
itens = DataItem(**config.DATABASE)
materials = DataMaterial(**config.DATABASE)
verifications = DataVerification(**config.DATABASE)
permissions = DataPermission(**config.DATABASE)
neural = Neural(config.MODEL_PATH)


# ----------------------------------------------------------------------------
# Acesso: quem está logado e o que cada um pode fazer
#
#   current_user                  rota que exige apenas estar logado
#   require_permission("chave")   rota que exige uma permissão (ver models/permissions.py)
#   current_manager               rota que só o gestor acessa, sem poder ser liberada
# ----------------------------------------------------------------------------
_bearer = HTTPBearer(auto_error=False)


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    """Usado nas rotas que exigem login. Devolve o usuário dono do token."""
    error = HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido, expirado ou ausente.")

    if credentials is None:
        raise error

    user_id = read_token(credentials.credentials, config.JWT_SECRET)
    if user_id is None:
        raise error

    # O usuário é sempre lido do banco, assim um usuário desativado perde o acesso na hora.
    success, user = users.find_by_id(user_id)
    if not success or user["status"] != "active":
        raise error

    return user


def current_manager(user: dict = Depends(current_user)) -> dict:
    """Usado nas rotas que só o gestor pode acessar, como liberar e retirar permissões."""
    if user["role"] != "gestor":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Apenas gestores podem fazer isso.")
    return user


def user_permissions(user: dict) -> list:
    """Lista de permissões do usuário. O gestor tem todas."""
    if user["role"] == "gestor":
        return list(DataPermission.PERMISSIONS)

    _, granted = permissions.list_by_user(user["id"])
    return granted


def has_permission(user: dict, permission: str) -> bool:
    return permission in user_permissions(user)


def require_permission(permission: str):
    """
    Cria a checagem de uma permissão para ser usada na rota.

    Exemplo:
        def create_item(..., _user: dict = Depends(require_permission("itens.create"))):

    A permissão é lida do banco a cada requisição, então liberar ou retirar vale na hora.
    """
    def check(user: dict = Depends(current_user)) -> dict:
        if not has_permission(user, permission):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Você não tem permissão para fazer isso.")
        return user

    return check


def create_initial_manager() -> None:
    """Sem isso ninguém consegue entrar na primeira vez, pois só o gestor cadastra usuários."""
    if users.has_manager():
        return

    users.create(config.ADMIN_NAME, config.ADMIN_EMAIL.lower(), hash_password(config.ADMIN_PASSWORD), "gestor")


# ----------------------------------------------------------------------------
# Aplicação FastAPI
# ----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(_api: FastAPI):
    """Roda uma vez quando o servidor sobe."""
    create_initial_manager()
    yield


API = FastAPI(
    title="Inventário por Foto - API",
    description="API para inventário por foto: o usuário fotografa, o modelo de IA conta os itens, e fica registrado quem contou o quê.",
    version=config.VERSION,
    lifespan=lifespan,
)

# Libera o front-end (que roda em outro endereço) para chamar a API.
API.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)


@API.get("/health", tags=["health"])
def health_check() -> dict:
    """Rota de saúde, para monitoramento saber se a API está no ar."""
    return {"status": "ok"}
