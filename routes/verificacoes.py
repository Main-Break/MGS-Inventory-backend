"""Verificações: o funcionário manda as fotos, o modelo conta, e fica registrado quem contou o quê."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

import config
import neural
import seguranca
from database import Banco, banco
from models.user import Usuario
from models.verificacao import Aprovacao, ContagemManual, ItemContado, Verificacao

router = APIRouter(prefix="/verifications", tags=["verifications"])

_EXTENSOES_VALIDAS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
_PASTA_UPLOAD = Path(config.UPLOAD_DIR)

_CONSULTA_BASE = """
    v.id, v.user_id, autor.name AS user_name, v.expected_item_id,
    esperado.label AS expected_item_label, v.manual_count, v.approved,
    v.approved_by, aprovador.name AS approved_by_name, v.approved_at,
    v.approval_note, v.created_at
    FROM verifications v
    JOIN users autor ON autor.id = v.user_id
    LEFT JOIN items esperado ON esperado.id = v.expected_item_id
    LEFT JOIN users aprovador ON aprovador.id = v.approved_by
"""


def _salvar_foto(arquivo: UploadFile) -> Path:
    extensao = Path(arquivo.filename or "").suffix.lower()
    if extensao not in _EXTENSOES_VALIDAS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extensão de imagem não suportada: '{extensao}'.",
        )

    conteudo = arquivo.file.read()
    if not conteudo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arquivo de imagem vazio.")
    if len(conteudo) > config.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Imagem maior que o limite de {config.MAX_UPLOAD_SIZE_MB}MB.",
        )

    _PASTA_UPLOAD.mkdir(parents=True, exist_ok=True)
    # O nome é gerado aqui, nunca o que veio do cliente: isso evita que
    # alguém escreva fora da pasta de upload ou sobrescreva outra foto.
    caminho = _PASTA_UPLOAD / f"{uuid.uuid4().hex}{extensao}"
    caminho.write_bytes(conteudo)
    return caminho


def _montar(db: Banco, linha: dict) -> Verificacao:
    """Junta a verificação com as fotos e a contagem por item."""
    fotos = db.buscar_todos(
        "SELECT image_filename FROM verification_photos WHERE verification_id = :id ORDER BY id",
        {"id": linha["id"]},
    )
    contados = db.buscar_todos(
        """
        SELECT vi.item_id, vi.label, vi.count, vi.avg_confidence, i.name AS item_name
        FROM verification_items vi
        LEFT JOIN items i ON i.id = vi.item_id
        WHERE vi.verification_id = :id
        ORDER BY vi.id
        """,
        {"id": linha["id"]},
    )

    itens = []
    for contado in contados:
        # A comparação com a recontagem manual só faz sentido para o item que
        # o funcionário disse que ia contar.
        precisao_manual = None
        if linha["manual_count"] is not None and contado["item_id"] == linha["expected_item_id"]:
            maior = max(contado["count"], linha["manual_count"], 1)
            diferenca = abs(contado["count"] - linha["manual_count"])
            precisao_manual = round(100 - diferenca / maior * 100, 1)

        itens.append(
            ItemContado(
                item_id=contado["item_id"],
                label=contado["label"],
                item_name=contado["item_name"],
                count=contado["count"],
                ai_confidence_pct=round(contado["avg_confidence"] * 100, 1),
                manual_accuracy_pct=precisao_manual,
            )
        )

    # Só dá para dizer que divergiu quando o funcionário informou o que esperava contar.
    diverge = None
    if linha["expected_item_label"] is not None:
        diverge = {item.label for item in itens} != {linha["expected_item_label"]}

    return Verificacao(
        **linha,
        diverge_do_esperado=diverge,
        photos=[foto["image_filename"] for foto in fotos],
        items=itens,
    )


def _buscar(db: Banco, verificacao_id: int) -> dict | None:
    return db.buscar_um(f"SELECT {_CONSULTA_BASE} WHERE v.id = :id", {"id": verificacao_id})


def _exigir(db: Banco, verificacao_id: int) -> dict:
    linha = _buscar(db, verificacao_id)
    if linha is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verificação {verificacao_id} não encontrada.",
        )
    return linha


@router.post("", response_model=Verificacao, status_code=status.HTTP_201_CREATED)
def criar_verificacao(
    files: list[UploadFile] = File(...),
    expected_item_id: int | None = Form(default=None),
    usuario: Usuario = Depends(seguranca.usuario_logado),
) -> Verificacao:
    """Recebe uma ou mais fotos de uma vez, conta os itens em cada uma e soma
    por label. Fica assinada por quem enviou."""
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Envie ao menos uma foto.")

    with banco() as db:
        if expected_item_id is not None:
            if db.buscar_um("SELECT id FROM items WHERE id = :id", {"id": expected_item_id}) is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Item {expected_item_id} não encontrado.",
                )

    caminhos = [_salvar_foto(arquivo) for arquivo in files]

    try:
        deteccoes_por_foto = [neural.contar_itens(caminho) for caminho in caminhos]
    except neural.ModeloIndisponivelError as erro:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(erro)
        ) from erro

    # Soma a contagem de cada label entre todas as fotos. A confiança média
    # é ponderada pela quantidade detectada em cada foto, para uma foto com
    # 2 peças não pesar o mesmo que outra com 50.
    total_por_label: dict[str, int] = {}
    soma_confianca: dict[str, float] = {}
    for deteccoes in deteccoes_por_foto:
        for deteccao in deteccoes:
            label = deteccao["label"]
            total_por_label[label] = total_por_label.get(label, 0) + deteccao["count"]
            soma_confianca[label] = soma_confianca.get(label, 0.0) + deteccao["count"] * deteccao["avg_confidence"]

    with banco() as db:
        verificacao_id = db.executar(
            "INSERT INTO verifications (user_id, expected_item_id) VALUES (:user_id, :expected_item_id)",
            {"user_id": usuario.id, "expected_item_id": expected_item_id},
        )

        for caminho in caminhos:
            db.executar(
                "INSERT INTO verification_photos (verification_id, image_filename) "
                "VALUES (:verification_id, :image_filename)",
                {"verification_id": verificacao_id, "image_filename": caminho.name},
            )

        for label, total in total_por_label.items():
            item = db.buscar_um("SELECT id FROM items WHERE label = :label", {"label": label})
            db.executar(
                """
                INSERT INTO verification_items (verification_id, item_id, label, count, avg_confidence)
                VALUES (:verification_id, :item_id, :label, :count, :avg_confidence)
                """,
                {
                    "verification_id": verificacao_id,
                    "item_id": item["id"] if item else None,
                    "label": label,
                    "count": total,
                    "avg_confidence": soma_confianca[label] / total if total else 0.0,
                },
            )

        return _montar(db, _exigir(db, verificacao_id))


@router.get("", response_model=list[Verificacao])
def listar_verificacoes(
    approved: bool | None = None, usuario: Usuario = Depends(seguranca.usuario_logado)
) -> list[Verificacao]:
    """O funcionário vê só as dele; o gestor vê as de todo mundo."""
    with banco() as db:
        if usuario.role == "gestor":
            linhas = db.buscar_todos(f"SELECT {_CONSULTA_BASE} ORDER BY v.id DESC")
        else:
            linhas = db.buscar_todos(
                f"SELECT {_CONSULTA_BASE} WHERE v.user_id = :user_id ORDER BY v.id DESC",
                {"user_id": usuario.id},
            )

        verificacoes = [_montar(db, linha) for linha in linhas]

    if approved is not None:
        verificacoes = [v for v in verificacoes if v.approved == approved]
    return verificacoes


@router.get("/{verificacao_id}", response_model=Verificacao)
def obter_verificacao(
    verificacao_id: int, usuario: Usuario = Depends(seguranca.usuario_logado)
) -> Verificacao:
    with banco() as db:
        linha = _exigir(db, verificacao_id)
        if usuario.role != "gestor" and linha["user_id"] != usuario.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Sem acesso a essa verificação."
            )
        return _montar(db, linha)


@router.patch("/{verificacao_id}/manual-count", response_model=Verificacao)
def informar_contagem_manual(
    verificacao_id: int,
    dados: ContagemManual,
    usuario: Usuario = Depends(seguranca.usuario_logado),
) -> Verificacao:
    """A recontagem na mão, para comparar com o que a IA contou. Só quem fez a
    verificação informa a dela."""
    with banco() as db:
        linha = _exigir(db, verificacao_id)

        if linha["user_id"] != usuario.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Só quem fez a verificação pode informar a contagem manual dela.",
            )
        if linha["expected_item_id"] is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Essa verificação não tem item esperado para comparar a contagem manual.",
            )

        db.executar(
            "UPDATE verifications SET manual_count = :manual_count WHERE id = :id",
            {"manual_count": dados.manual_count, "id": verificacao_id},
        )
        return _montar(db, _exigir(db, verificacao_id))


@router.patch("/{verificacao_id}/approval", response_model=Verificacao)
def revisar_verificacao(
    verificacao_id: int, dados: Aprovacao, gestor: Usuario = Depends(seguranca.gestor_logado)
) -> Verificacao:
    """Revisão do gestor. É opcional: fica nulo enquanto ninguém revisar."""
    with banco() as db:
        _exigir(db, verificacao_id)
        db.executar(
            """
            UPDATE verifications
            SET approved = :approved, approved_by = :approved_by,
                approved_at = CURRENT_TIMESTAMP, approval_note = :approval_note
            WHERE id = :id
            """,
            {
                "approved": dados.approved,
                "approved_by": gestor.id,
                "approval_note": dados.approval_note,
                "id": verificacao_id,
            },
        )
        return _montar(db, _exigir(db, verificacao_id))
