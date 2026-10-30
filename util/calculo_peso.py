"""
Cálculo do peso teórico de um item a partir da geometria e da densidade do material.

Mesma conta usada pela tabela de pesos e medidas da MGS (peso = volume × densidade):
cada formato lê height_cm/width_cm/length_cm de um jeito diferente (ver o comentário
de "shape" em database/database.sql). Este arquivo não conhece banco nem rotas, só
faz a conta, igual util/security.py.
"""

import math

SHAPES = ["bastao_redondo", "bastao_quadrado", "tubo", "chapa"]


def _volume_cm3(shape: str, height_cm: float | None, width_cm: float | None, length_cm: float | None) -> float:
    if shape == "bastao_redondo":
        # width_cm é o diâmetro, length_cm é o comprimento.
        raio = (width_cm or 0) / 2
        return math.pi * (raio ** 2) * (length_cm or 0)

    if shape == "bastao_quadrado":
        # height_cm é o lado, length_cm é o comprimento.
        lado = height_cm or 0
        return (lado ** 2) * (length_cm or 0)

    if shape == "tubo":
        # width_cm é o diâmetro externo, height_cm é o diâmetro interno.
        raio_externo = (width_cm or 0) / 2
        raio_interno = (height_cm or 0) / 2
        return math.pi * (raio_externo ** 2 - raio_interno ** 2) * (length_cm or 0)

    if shape == "chapa":
        # height_cm é a espessura, width_cm é a largura, length_cm é o comprimento.
        return (height_cm or 0) * (width_cm or 0) * (length_cm or 0)

    raise ValueError(f"Formato desconhecido: {shape}")


def peso_kg(shape: str, density_g_cm3: float, height_cm: float | None, width_cm: float | None, length_cm: float | None) -> float:
    """
    Peso teórico em quilos. density_g_cm3 é a densidade do material (models/materials.py).
    Dimensões que faltarem contam como zero, então falta de medida vira peso zero, não erro.
    """
    if shape not in SHAPES:
        raise ValueError(f"Formato desconhecido: {shape}")

    volume_cm3 = _volume_cm3(shape, height_cm, width_cm, length_cm)
    gramas = volume_cm3 * density_g_cm3
    return round(gramas / 1000, 3)
