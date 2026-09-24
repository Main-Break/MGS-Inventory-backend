"""Contagem de itens na foto usando o modelo YOLO treinado.

Enquanto não existir um arquivo .pt em MODEL_PATH, a contagem levanta
ModeloIndisponivelError e a rota responde 503. Quando o modelo for colocado
lá, passa a funcionar sem mudar nada aqui.
"""

from pathlib import Path
from threading import Lock

import config

_modelo = None
_lock = Lock()


class ModeloIndisponivelError(Exception):
    pass


def _carregar_modelo():
    """Carrega o .pt uma vez só e guarda em memória (carregar é lento)."""
    global _modelo

    if _modelo is not None:
        return _modelo

    caminho = Path(config.MODEL_PATH)
    if not caminho.is_file():
        raise ModeloIndisponivelError(
            f"Modelo de detecção não encontrado em '{caminho}'. "
            "Coloque o arquivo .pt nesse caminho ou ajuste MODEL_PATH no .env."
        )

    # Importado só aqui porque o ultralytics é pesado: a API sobe e funciona
    # sem ele instalado, e só a contagem por foto fica indisponível.
    from ultralytics import YOLO

    with _lock:
        if _modelo is None:
            _modelo = YOLO(str(caminho))
    return _modelo


def contar_itens(caminho_imagem: Path) -> list[dict]:
    """Roda o modelo numa foto e devolve, por classe detectada, quantas peças
    apareceram e a confiança média (0 a 1) que o modelo deu para elas."""
    modelo = _carregar_modelo()
    resultado = modelo(source=str(caminho_imagem))[0]

    confiancas_por_classe: dict[str, list[float]] = {}
    for classe_id, confianca in zip(resultado.boxes.cls.tolist(), resultado.boxes.conf.tolist()):
        nome_classe = modelo.names[int(classe_id)]
        confiancas_por_classe.setdefault(nome_classe, []).append(confianca)

    return [
        {
            "label": label,
            "count": len(confiancas),
            "avg_confidence": sum(confiancas) / len(confiancas),
        }
        for label, confiancas in confiancas_por_classe.items()
    ]
