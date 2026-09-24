"""Treina o modelo de detecção a partir de um dataset em formato YOLO.

Roda na mão, fora da API (treino é demorado e não pode travar quem está
usando o sistema):

    python treinar.py caminho/do/dataset.yaml

No fim copia o melhor peso gerado para o MODEL_PATH do .env, que é de onde
a API carrega o modelo.
"""

import shutil
import sys
from pathlib import Path

import config

EPOCAS = 50
TAMANHO_IMAGEM = 640
MODELO_BASE = "yolo11n.pt"  # pesos pré-treinados, baixados na primeira vez


def treinar(caminho_dataset: str, epocas: int = EPOCAS) -> None:
    dataset = Path(caminho_dataset)
    if not dataset.is_file():
        raise FileNotFoundError(f"dataset não encontrado: {dataset}")

    from ultralytics import YOLO

    modelo = YOLO(MODELO_BASE)
    resultado = modelo.train(
        data=str(dataset),
        epochs=epocas,
        imgsz=TAMANHO_IMAGEM,
        project=str(dataset.parent / "execucoes"),
        name="treino",
        exist_ok=True,
    )

    melhor_peso = Path(resultado.save_dir) / "weights" / "best.pt"
    if not melhor_peso.is_file():
        raise RuntimeError(f"o treino terminou mas não achei os pesos em '{melhor_peso}'")

    destino = Path(config.MODEL_PATH)
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(melhor_peso, destino)
    print(f"\nmodelo salvo em: {destino}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("uso: python treinar.py caminho/do/dataset.yaml")
        raise SystemExit(1)
    treinar(sys.argv[1])
