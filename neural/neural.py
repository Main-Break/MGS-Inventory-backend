"""Detecção e contagem de itens numa foto, usando o modelo YOLO treinado.

Enquanto não existir um .pt em MODEL_PATH, contar_itens() levanta
ModeloIndisponivelError (a rota devolve 503).
"""

from pathlib import Path


class ModeloIndisponivelError(Exception):
    pass


class Neural:
    def __init__(self, model_path: str):
        self._model_path = model_path
        self._modelo = None

    def _carregar_modelo(self):
        if self._modelo is None:
            if not Path(self._model_path).is_file():
                raise ModeloIndisponivelError(
                    f"Modelo de detecção não encontrado em '{self._model_path}'."
                )

            from ultralytics import YOLO  # pesado, só importa se o modelo existir

            self._modelo = YOLO(self._model_path)

        return self._modelo

    def contar_itens(self, caminho_imagem: Path) -> list[dict]:
        modelo = self._carregar_modelo()
        resultado = modelo(source=str(caminho_imagem))[0]

        confiancas_por_classe: dict[str, list[float]] = {}
        for classe_id, confianca in zip(resultado.boxes.cls.tolist(), resultado.boxes.conf.tolist()):
            nome_classe = modelo.names[int(classe_id)]
            confiancas_por_classe.setdefault(nome_classe, []).append(confianca)

        return [
            {"label": label, "count": len(confiancas), "confidence": sum(confiancas) / len(confiancas)}
            for label, confiancas in confiancas_por_classe.items()
        ]
