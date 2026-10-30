"""
Reconhecimento e contagem de itens em uma foto, usando o modelo YOLO treinado.

A classe Neural é criada uma vez no core.py e usada pelas rotas.
Enquanto não existir o arquivo do modelo (.pt) em MODEL_PATH, count_items()
levanta ModelUnavailableError e a rota responde 503 (serviço indisponível).
"""

from pathlib import Path


class ModelUnavailableError(Exception):
    """O modelo treinado ainda não existe no caminho configurado."""


class Neural:

    def __init__(self, model_path: str) -> None:
        self._model_path = model_path
        self._model = None

    def is_available(self) -> bool:
        """Diz se o arquivo do modelo treinado existe."""
        return Path(self._model_path).is_file()

    def load_model(self):
        """Carrega o modelo só na primeira vez que for usado, pois é pesado."""
        if self._model is None:
            if not self.is_available():
                raise ModelUnavailableError(f"Modelo de detecção não encontrado em '{self._model_path}'.")

            # Importa aqui dentro, pois o ultralytics traz o PyTorch junto e é pesado.
            from ultralytics import YOLO

            self._model = YOLO(self._model_path)

        return self._model

    def count_items(self, image_path: Path) -> list[dict]:
        """
        Reconhece os itens da foto e conta quantos tem de cada um.

        Retorna uma lista, ex:
            [{"label": "garrafa_pet", "count": 12, "confidence": 0.91}]
        confidence é a média de certeza da IA para aquele item (0 a 1).
        """
        model = self.load_model()
        result = model(source=str(image_path))[0]

        # Junta as certezas de cada item reconhecido, separadas pelo label.
        confidences_by_label: dict[str, list[float]] = {}
        for class_id, confidence in zip(result.boxes.cls.tolist(), result.boxes.conf.tolist()):
            label = model.names[int(class_id)]
            confidences_by_label.setdefault(label, []).append(confidence)

        return [
            {"label": label, "count": len(confidences), "confidence": sum(confidences) / len(confidences)}
            for label, confidences in confidences_by_label.items()
        ]
