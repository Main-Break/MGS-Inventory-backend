"""Cadastro, listagem e edição de usuários."""

from fastapi import APIRouter, Depends, HTTPException, status

from core import banco
from models import Usuario, UsuarioAtualizar, UsuarioCriar
from security import gerar_hash_senha, gestor_logado, usuario_logado

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=Usuario, status_code=status.HTTP_201_CREATED)
def criar_usuario(dados: UsuarioCriar, _gestor: dict = Depends(gestor_logado)) -> dict:
    with banco() as db:
        if db.buscar_um("SELECT id FROM users WHERE email = ?", (dados.email.lower(),)):
            raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um usuário com esse e-mail.")

        novo_id = db.executar(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (dados.name, dados.email.lower(), gerar_hash_senha(dados.password), dados.role),
        )
        return db.buscar_um("SELECT * FROM users WHERE id = ?", (novo_id,))


@router.get("", response_model=list[Usuario])
def listar_usuarios(_gestor: dict = Depends(gestor_logado)) -> list[dict]:
    with banco() as db:
        return db.buscar_todos("SELECT * FROM users ORDER BY id")


@router.get("/me", response_model=Usuario)
def meus_dados(usuario: dict = Depends(usuario_logado)) -> dict:
    return usuario


@router.put("/me", response_model=Usuario)
def atualizar_meus_dados(dados: UsuarioAtualizar, usuario: dict = Depends(usuario_logado)) -> dict:
    senha_hash = gerar_hash_senha(dados.password) if dados.password else usuario["password_hash"]
    with banco() as db:
        db.executar(
            "UPDATE users SET name = ?, email = ?, password_hash = ? WHERE id = ?",
            (dados.name, dados.email.lower(), senha_hash, usuario["id"]),
        )
        return db.buscar_um("SELECT * FROM users WHERE id = ?", (usuario["id"],))


@router.patch("/{usuario_id}/active", response_model=Usuario)
def mudar_acesso(usuario_id: int, ativo: bool, _gestor: dict = Depends(gestor_logado)) -> dict:
    with banco() as db:
        if db.buscar_um("SELECT id FROM users WHERE id = ?", (usuario_id,)) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado.")
        db.executar("UPDATE users SET active = ? WHERE id = ?", (ativo, usuario_id))
        return db.buscar_um("SELECT * FROM users WHERE id = ?", (usuario_id,))
