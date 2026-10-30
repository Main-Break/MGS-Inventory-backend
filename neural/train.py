"""
Treinamento do modelo YOLO a partir de um dataset em formato YOLO (arquivo .yaml).

Usado pelo CLI. No final, o melhor peso gerado é copiado para MODEL_PATH,
que é o modelo usado pela classe Neural nas verificações.
"""

import shutil
from pathlib import Path


class Train:

    def __init__(self, model_path: str, runs_dir: str, base_model: str = "yolo11n.pt", epochs: int = 50) -> None:
        self._model_path = Path(model_path)  # para onde vai o modelo final
        self._runs_dir = Path(runs_dir)      # onde o YOLO guarda os arquivos de cada treino
        self._base_model = base_model        # modelo de partida do YOLO
        self._epochs = epochs                # quantas vezes o treino passa pelo dataset

    def run(self, dataset_path: str) -> Path:
        """Treina com o dataset informado e devolve o caminho do modelo salvo."""
        # Importa aqui dentro, pois o ultralytics traz o PyTorch junto e é pesado.
        from ultralytics import YOLO

        model = YOLO(self._base_model)
        result = model.train(
            data=dataset_path,
            epochs=self._epochs,
            project=str(self._runs_dir),
            name="treino",
            exist_ok=True
        )

        best_weight = Path(result.save_dir) / "weights" / "best.pt"
        self._model_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(best_weight, self._model_path)

        print(f"Modelo salvo em: {self._model_path}")
        return self._model_path
