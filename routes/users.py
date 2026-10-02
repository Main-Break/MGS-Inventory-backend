"""Cadastro, listagem e edição de usuários."""

from fastapi import APIRouter, Depends, HTTPException, status

import core
from models.user import EmailJaCadastradoError, User
from schemas import Usuario, UsuarioAtualizar, UsuarioCriar
from security import gerar_hash_senha, gestor_logado, usuario_logado

router = APIRouter(prefix="/users", tags=["users"])


def _usuarios() -> User:
    return User(core.DB_FILE)


@router.post("", response_model=Usuario, status_code=status.HTTP_201_CREATED)
def criar_usuario(dados: UsuarioCriar, _gestor: dict = Depends(gestor_logado)) -> dict:
    try:
        return _usuarios().criar(dados.name, dados.email.lower(), gerar_hash_senha(dados.password), dados.role)
    except EmailJaCadastradoError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um usuário com esse e-mail.") from None


@router.get("", response_model=list[Usuario])
def listar_usuarios(_gestor: dict = Depends(gestor_logado)) -> list[dict]:
    return _usuarios().listar()


@router.get("/me", response_model=Usuario)
def meus_dados(usuario: dict = Depends(usuario_logado)) -> dict:
    return usuario


@router.put("/me", response_model=Usuario)
def atualizar_meus_dados(dados: UsuarioAtualizar, usuario: dict = Depends(usuario_logado)) -> dict:
    senha_hash = gerar_hash_senha(dados.password) if dados.password else usuario["password_hash"]
    return _usuarios().atualizar(usuario["id"], dados.name, dados.email.lower(), senha_hash)


@router.patch("/{usuario_id}/active", response_model=Usuario)
def mudar_acesso(usuario_id: int, ativo: bool, _gestor: dict = Depends(gestor_logado)) -> dict:
    usuario = _usuarios().mudar_acesso(usuario_id, ativo)
    if usuario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado.")
    return usuario
