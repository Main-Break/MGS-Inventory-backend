"""Detecção e contagem de itens numa foto, usando o modelo YOLO treinado.

Enquanto não existir um .pt em MODEL_PATH, count_items() levanta
ModelUnavailableError (a rota devolve 503).
"""

from pathlib import Path


class ModelUnavailableError(Exception):
    pass


class Neural:
    def __init__(self, model_path: str):
        self._model_path = model_path
        self._model = None

    def _load_model(self):
        if self._model is None:
            if not Path(self._model_path).is_file():
                raise ModelUnavailableError(
                    f"Modelo de detecção não encontrado em '{self._model_path}'."
                )

            from ultralytics import YOLO  # pesado, só importa se o modelo existir

            self._model = YOLO(self._model_path)

        return self._model

    def count_items(self, image_path: Path) -> list[dict]:
        model = self._load_model()
        result = model(source=str(image_path))[0]

        confidences_by_class: dict[str, list[float]] = {}
        for class_id, confidence in zip(result.boxes.cls.tolist(), result.boxes.conf.tolist()):
            class_name = model.names[int(class_id)]
            confidences_by_class.setdefault(class_name, []).append(confidence)

        return [
            {"label": label, "count": len(confidences), "confidence": sum(confidences) / len(confidences)}
            for label, confidences in confidences_by_class.items()
        ]
