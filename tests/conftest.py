"""
Configuração dos testes: banco de teste separado e cliente da API.

Os testes rodam contra um banco MySQL/MariaDB de verdade (DB_NAME_TEST do
.env), não contra mocks, para testar exatamente o SQL que vai para produção.
Antes de qualquer coisa, a variável DB_NAME é trocada para o banco de teste,
e só então core.py é importado (é ele que lê o .env e monta a conexão).
"""

import os

os.environ["DB_NAME"] = os.getenv("DB_NAME_TEST", "inventario_test")

import mysql.connector
import pytest
from fastapi.testclient import TestClient

from core import API, config
from database.migrate import apply_schema
from register import register_routes

# As rotas só existem no app depois de registradas (o mesmo que main.py faz para subir o servidor).
register_routes(API)

# Ordem de limpeza respeita as chaves estrangeiras (user_permissions e
# verifications apontam para users; itens aponta para materials).
TABLES = ["user_permissions", "verifications", "itens", "materials", "users"]


def clean_tables() -> None:
    conn = mysql.connector.connect(**config.DATABASE)
    cursor = conn.cursor()
    for table in TABLES:
        cursor.execute(f"DELETE FROM {table}")
    conn.commit()
    cursor.close()
    conn.close()


@pytest.fixture(scope="session", autouse=True)
def schema():
    """O esquema do banco de teste é aplicado uma vez, no início da sessão de testes."""
    apply_schema(**config.DATABASE)


@pytest.fixture(autouse=True)
def database(schema):
    """Cada teste começa e termina com o banco de teste vazio."""
    clean_tables()
    yield
    clean_tables()


@pytest.fixture
def client():
    """
    O "with" aciona o lifespan de core.py (aplica o esquema e cria o gestor
    inicial com as credenciais ADMIN_* do .env), igual à subida real da API.
    """
    with TestClient(API) as test_client:
        yield test_client


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def manager_token(client) -> str:
    """Token do gestor criado pelo lifespan (ADMIN_EMAIL / ADMIN_PASSWORD do .env)."""
    response = client.post("/auth/login", json={"email": config.ADMIN_EMAIL, "password": config.ADMIN_PASSWORD})
    return response.json()["access_token"]


@pytest.fixture
def employee_token(client, manager_token) -> str:
    """Token de um funcionário novo, sem nenhuma permissão extra."""
    client.post(
        "/users",
        json={"name": "Funcionário Teste", "email": "funcionario@teste.com", "password": "senha12345", "role": "funcionario"},
        headers=auth_headers(manager_token),
    )
    response = client.post("/auth/login", json={"email": "funcionario@teste.com", "password": "senha12345"})
    return response.json()["access_token"]
