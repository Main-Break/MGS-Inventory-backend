"""API de inventário por foto: usuário fotografa, o modelo de IA conta os
itens, e fica registrado quem contou o quê."""

import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status

import ai
import config
from database import banco, criar_tabelas
from models import (
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


app = FastAPI(title="Inventário por Foto - API", lifespan=ciclo_de_vida)

_EXTENSOES_VALIDAS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


# --- Autenticação ---


@app.post("/auth/login", response_model=Token, tags=["auth"])
def login(dados: Login) -> dict:
    with banco() as db:
        usuario = db.buscar_um("SELECT * FROM users WHERE email = ?", (dados.email.lower(),))

    if usuario is None or not conferir_senha(dados.password, usuario["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha inválidos.")
    if not usuario["active"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Usuário desativado.")

    return {"access_token": criar_token(usuario["id"], usuario["role"])}


# --- Usuários ---


@app.post("/users", response_model=Usuario, status_code=status.HTTP_201_CREATED, tags=["users"])
def criar_usuario(dados: UsuarioCriar, _gestor: dict = Depends(gestor_logado)) -> dict:
    with banco() as db:
        if db.buscar_um("SELECT id FROM users WHERE email = ?", (dados.email.lower(),)):
            raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um usuário com esse e-mail.")

        novo_id = db.executar(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (dados.name, dados.email.lower(), gerar_hash_senha(dados.password), dados.role),
        )
        return db.buscar_um("SELECT * FROM users WHERE id = ?", (novo_id,))


@app.get("/users", response_model=list[Usuario], tags=["users"])
def listar_usuarios(_gestor: dict = Depends(gestor_logado)) -> list[dict]:
    with banco() as db:
        return db.buscar_todos("SELECT * FROM users ORDER BY id")


@app.get("/users/me", response_model=Usuario, tags=["users"])
def meus_dados(usuario: dict = Depends(usuario_logado)) -> dict:
    return usuario


@app.put("/users/me", response_model=Usuario, tags=["users"])
def atualizar_meus_dados(dados: UsuarioAtualizar, usuario: dict = Depends(usuario_logado)) -> dict:
    senha_hash = gerar_hash_senha(dados.password) if dados.password else usuario["password_hash"]
    with banco() as db:
        db.executar(
            "UPDATE users SET name = ?, email = ?, password_hash = ? WHERE id = ?",
            (dados.name, dados.email.lower(), senha_hash, usuario["id"]),
        )
        return db.buscar_um("SELECT * FROM users WHERE id = ?", (usuario["id"],))


@app.patch("/users/{usuario_id}/active", response_model=Usuario, tags=["users"])
def mudar_acesso(usuario_id: int, ativo: bool, _gestor: dict = Depends(gestor_logado)) -> dict:
    with banco() as db:
        if db.buscar_um("SELECT id FROM users WHERE id = ?", (usuario_id,)) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado.")
        db.executar("UPDATE users SET active = ? WHERE id = ?", (ativo, usuario_id))
        return db.buscar_um("SELECT * FROM users WHERE id = ?", (usuario_id,))


# --- Itens ---


@app.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED, tags=["items"])
def criar_item(dados: ItemCriar, _gestor: dict = Depends(gestor_logado)) -> dict:
    with banco() as db:
        if db.buscar_um("SELECT id FROM items WHERE label = ?", (dados.label,)):
            raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um item com esse label.")

        novo_id = db.executar(
            "INSERT INTO items (label, name, stock_quantity) VALUES (?, ?, ?)",
            (dados.label, dados.name, dados.stock_quantity),
        )
        return db.buscar_um("SELECT * FROM items WHERE id = ?", (novo_id,))


@app.get("/items", response_model=list[Item], tags=["items"])
def buscar_itens(q: str | None = None, _usuario: dict = Depends(usuario_logado)) -> list[dict]:
    with banco() as db:
        if q:
            return db.buscar_todos(
                "SELECT * FROM items WHERE name LIKE ? OR label LIKE ? ORDER BY name",
                (f"%{q}%", f"%{q}%"),
            )
        return db.buscar_todos("SELECT * FROM items ORDER BY name")


@app.get("/items/{item_id}", response_model=Item, tags=["items"])
def obter_item(item_id: int, _usuario: dict = Depends(usuario_logado)) -> dict:
    with banco() as db:
        item = db.buscar_um("SELECT * FROM items WHERE id = ?", (item_id,))
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item não encontrado.")
    return item


# --- Verificações (foto + contagem pela IA) ---


def _montar_verificacao(linha: dict) -> dict:
    return {**linha, "detections": [Deteccao(**d) for d in json.loads(linha["detections"])]}


@app.post("/verifications", response_model=Verificacao, status_code=status.HTTP_201_CREATED, tags=["verifications"])
def criar_verificacao(
    file: UploadFile = File(...),
    item_id: int | None = Form(default=None),
    usuario: dict = Depends(usuario_logado),
) -> dict:
    extensao = Path(file.filename or "").suffix.lower()
    if extensao not in _EXTENSOES_VALIDAS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Extensão de imagem não suportada: '{extensao}'.")

    conteudo = file.file.read()
    if not conteudo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Arquivo de imagem vazio.")

    Path(config.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    # Nome gerado aqui, nunca o do cliente: evita path traversal e sobrescrita.
    nome_arquivo = f"{uuid.uuid4().hex}{extensao}"
    (Path(config.UPLOAD_DIR) / nome_arquivo).write_bytes(conteudo)

    try:
        deteccoes = ai.contar_itens(Path(config.UPLOAD_DIR) / nome_arquivo)
    except ai.ModeloIndisponivelError as erro:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(erro)) from erro

    with banco() as db:
        novo_id = db.executar(
            "INSERT INTO verifications (user_id, item_id, photo_filename, detections) VALUES (?, ?, ?, ?)",
            (usuario["id"], item_id, nome_arquivo, json.dumps(deteccoes)),
        )
        return _montar_verificacao(db.buscar_um("SELECT * FROM verifications WHERE id = ?", (novo_id,)))


@app.get("/verifications", response_model=list[Verificacao], tags=["verifications"])
def listar_verificacoes(usuario: dict = Depends(usuario_logado)) -> list[dict]:
    with banco() as db:
        if usuario["role"] == "gestor":
            linhas = db.buscar_todos("SELECT * FROM verifications ORDER BY id DESC")
        else:
            linhas = db.buscar_todos(
                "SELECT * FROM verifications WHERE user_id = ? ORDER BY id DESC", (usuario["id"],)
            )
    return [_montar_verificacao(linha) for linha in linhas]


@app.get("/verifications/{verificacao_id}", response_model=Verificacao, tags=["verifications"])
def obter_verificacao(verificacao_id: int, usuario: dict = Depends(usuario_logado)) -> dict:
    with banco() as db:
        linha = db.buscar_um("SELECT * FROM verifications WHERE id = ?", (verificacao_id,))
    if linha is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Verificação não encontrada.")
    if usuario["role"] != "gestor" and linha["user_id"] != usuario["id"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sem acesso a essa verificação.")
    return _montar_verificacao(linha)


@app.patch("/verifications/{verificacao_id}/approve", response_model=Verificacao, tags=["verifications"])
def aprovar_verificacao(verificacao_id: int, aprovado: bool, _gestor: dict = Depends(gestor_logado)) -> dict:
    with banco() as db:
        if db.buscar_um("SELECT id FROM verifications WHERE id = ?", (verificacao_id,)) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Verificação não encontrada.")
        db.executar("UPDATE verifications SET approved = ? WHERE id = ?", (aprovado, verificacao_id))
        return _montar_verificacao(db.buscar_um("SELECT * FROM verifications WHERE id = ?", (verificacao_id,)))


if __name__ == "__main__":
    uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=True)
