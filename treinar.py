"""Treina o modelo a partir de um dataset em formato YOLO. Roda na mão:

    python treinar.py caminho/do/dataset.yaml

Copia o melhor peso gerado para o MODEL_PATH do .env no final.
"""

import shutil
import sys
from pathlib import Path

import config

EPOCAS = 50


def treinar(caminho_dataset: str) -> None:
    from ultralytics import YOLO

    modelo = YOLO("yolo11n.pt")
    resultado = modelo.train(data=caminho_dataset, epochs=EPOCAS, project="execucoes", name="treino", exist_ok=True)

    melhor_peso = Path(resultado.save_dir) / "weights" / "best.pt"
    destino = Path(config.MODEL_PATH)
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(melhor_peso, destino)
    print(f"modelo salvo em: {destino}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("uso: python treinar.py caminho/do/dataset.yaml")
        raise SystemExit(1)
    treinar(sys.argv[1])
