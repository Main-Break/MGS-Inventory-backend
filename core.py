"""Configurações lidas do .env."""

import os

from dotenv import load_dotenv

"""API de inventário por foto: usuário fotografa, o modelo de IA conta os
itens, e fica registrado quem contou o quê."""

import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status

import neural.ai as ai
from models.database import banco, criar_tabelas
from models.models import (
    Deteccao,
    Item,
    ItemCriar,
    Login,
    Token,
    Usuario,
    UsuarioAtualizar,
    UsuarioCriar,
    Verificacao,
)
from security import (
    conferir_senha,
    criar_gestor_inicial,
    criar_token,
    gerar_hash_senha,
    gestor_logado,
    usuario_logado,
)


@asynccontextmanager
async def ciclo_de_vida(_app: FastAPI):
    criar_tabelas()
    criar_gestor_inicial()
    yield


load_dotenv()

DB_FILE = os.getenv("DB_FILE", "inventario.db")
JWT_SECRET = os.getenv("JWT_SECRET", "troque-esta-chave-no-.env")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MODEL_PATH = os.getenv("MODEL_PATH", "modelos/producao.pt")

ADMIN_NAME = os.getenv("ADMIN_NAME", "Administrador")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@exemplo.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))


app = FastAPI(title="Inventário por Foto MGS - API", lifespan=ciclo_de_vida)

_EXTENSOES_VALIDAS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}