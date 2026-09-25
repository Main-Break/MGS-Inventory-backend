"""Detecção e contagem de itens numa foto, usando o modelo YOLO treinado.

Enquanto não existir um .pt em MODEL_PATH, contar_itens() levanta
ModeloIndisponivelError (a rota devolve 503).
"""

from pathlib import Path

import config

_modelo = None


class ModeloIndisponivelError(Exception):
    pass


def contar_itens(caminho_imagem: Path) -> list[dict]:
    global _modelo

    if _modelo is None:
        if not Path(config.MODEL_PATH).is_file():
            raise ModeloIndisponivelError(
                f"Modelo de detecção não encontrado em '{config.MODEL_PATH}'."
            )
        from ultralytics import YOLO  # pesado, só importa se o modelo existir

        _modelo = YOLO(config.MODEL_PATH)

    resultado = _modelo(source=str(caminho_imagem))[0]

    confiancas_por_classe: dict[str, list[float]] = {}
    for classe_id, confianca in zip(resultado.boxes.cls.tolist(), resultado.boxes.conf.tolist()):
        nome_classe = _modelo.names[int(classe_id)]
        confiancas_por_classe.setdefault(nome_classe, []).append(confianca)

    return [
        {"label": label, "count": len(confiancas), "confidence": sum(confiancas) / len(confiancas)}
        for label, confiancas in confiancas_por_classe.items()
    ]
