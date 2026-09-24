"""Usuários: o gestor cadastra e controla o acesso, cada um edita os próprios dados."""

from fastapi import APIRouter, Depends, HTTPException, status

import seguranca
from database import Banco, banco
from models.user import Usuario, UsuarioAtivo, UsuarioAtualizar, UsuarioCriar

router = APIRouter(prefix="/users", tags=["users"])

_COLUNAS = "id, name, email, role, active, created_at"


def _buscar(db: Banco, usuario_id: int) -> dict | None:
    return db.buscar_um(f"SELECT {_COLUNAS} FROM users WHERE id = :id", {"id": usuario_id})


def _email_em_uso(db: Banco, email: str, ignorar_id: int | None = None) -> bool:
    linha = db.buscar_um("SELECT id FROM users WHERE email = :email", {"email": email})
    return linha is not None and linha["id"] != ignorar_id


@router.post("", response_model=Usuario, status_code=status.HTTP_201_CREATED)
def criar_usuario(dados: UsuarioCriar, _gestor: Usuario = Depends(seguranca.gestor_logado)) -> Usuario:
    with banco() as db:
        if _email_em_uso(db, dados.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Já existe um usuário com o e-mail '{dados.email}'.",
            )

        novo_id = db.executar(
            """
            INSERT INTO users (name, email, password_hash, role, active)
            VALUES (:name, :email, :password_hash, :role, TRUE)
            """,
            {
                "name": dados.name,
                "email": dados.email,
                "password_hash": seguranca.gerar_hash_senha(dados.password),
                "role": dados.role,
            },
        )
        return Usuario(**_buscar(db, novo_id))


@router.get("", response_model=list[Usuario])
def listar_usuarios(_gestor: Usuario = Depends(seguranca.gestor_logado)) -> list[Usuario]:
    with banco() as db:
        return [Usuario(**linha) for linha in db.buscar_todos(f"SELECT {_COLUNAS} FROM users ORDER BY id")]


@router.get("/me", response_model=Usuario)
def meus_dados(usuario: Usuario = Depends(seguranca.usuario_logado)) -> Usuario:
    return usuario


@router.patch("/me", response_model=Usuario)
def atualizar_meus_dados(
    dados: UsuarioAtualizar, usuario: Usuario = Depends(seguranca.usuario_logado)
) -> Usuario:
    """Cada um muda só nome, e-mail e senha. Papel e acesso são do gestor."""
    campos = {"name": dados.name, "email": dados.email}
    if dados.password:
        campos["password_hash"] = seguranca.gerar_hash_senha(dados.password)
    campos = {coluna: valor for coluna, valor in campos.items() if valor is not None}

    with banco() as db:
        if dados.email and _email_em_uso(db, dados.email, ignorar_id=usuario.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Já existe um usuário com o e-mail '{dados.email}'.",
            )

        if campos:
            # Os nomes das colunas vêm daqui de dentro (nunca do que o cliente
            # mandou) e os valores continuam indo como parâmetro.
            atribuicoes = ", ".join(f"{coluna} = :{coluna}" for coluna in campos)
            db.executar(f"UPDATE users SET {atribuicoes} WHERE id = :id", {**campos, "id": usuario.id})

        return Usuario(**_buscar(db, usuario.id))


@router.get("/{usuario_id}", response_model=Usuario)
def obter_usuario(usuario_id: int, _gestor: Usuario = Depends(seguranca.gestor_logado)) -> Usuario:
    with banco() as db:
        linha = _buscar(db, usuario_id)
    if linha is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Usuário {usuario_id} não encontrado."
        )
    return Usuario(**linha)


@router.patch("/{usuario_id}/active", response_model=Usuario)
def ativar_ou_desativar(
    usuario_id: int, dados: UsuarioAtivo, _gestor: Usuario = Depends(seguranca.gestor_logado)
) -> Usuario:
    with banco() as db:
        if _buscar(db, usuario_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Usuário {usuario_id} não encontrado."
            )
        db.executar(
            "UPDATE users SET active = :active WHERE id = :id",
            {"active": dados.active, "id": usuario_id},
        )
        return Usuario(**_buscar(db, usuario_id))
