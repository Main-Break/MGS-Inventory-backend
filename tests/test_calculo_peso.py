"""
Cálculo de peso por geometria (util/calculo_peso.py).

O teste `test_bastao_redondo_bate_com_a_tabela_mgs` é ancorado na tabela oficial de
pesos e medidas da MGS (peso por metro linear, por isso usa comprimento de 100cm).
Os demais testam a fórmula com números exatos, calculados à mão, para não depender
da extração de uma tabela em PDF (que tem duas representações do mesmo dado, texto e
imagem, sujeitas a desalinhamento entre linha e coluna na extração automática).
"""

import math

import pytest

from util.calculo_peso import peso_kg

DENSIDADE_NY6 = 1.14  # Nylon 6, tabela MGS


def test_bastao_redondo_bate_com_a_tabela_mgs():
    # 20mm de diâmetro, Nylon 6: tabela MGS diz ~0.38 kg/m.
    peso = peso_kg("bastao_redondo", DENSIDADE_NY6, height_cm=0, width_cm=2, length_cm=100)

    assert peso == pytest.approx(0.38, rel=0.08)


def test_bastao_redondo_formula_exata():
    # raio 1cm, comprimento 100cm: volume = pi * 1^2 * 100 cm^3, densidade 1 g/cm^3.
    peso = peso_kg("bastao_redondo", 1.0, height_cm=0, width_cm=2, length_cm=100)

    assert peso == pytest.approx(math.pi * 100 / 1000, rel=0.001)


def test_bastao_quadrado_formula_exata():
    # lado 2cm, comprimento 100cm: volume = 2^2 * 100 = 400 cm^3, densidade 1 g/cm^3.
    peso = peso_kg("bastao_quadrado", 1.0, height_cm=2, width_cm=0, length_cm=100)

    assert peso == pytest.approx(0.4, rel=0.001)


def test_chapa_formula_exata():
    # espessura 1cm, largura 10cm, comprimento 20cm: volume = 200 cm^3, densidade 1 g/cm^3.
    peso = peso_kg("chapa", 1.0, height_cm=1, width_cm=10, length_cm=20)

    assert peso == pytest.approx(0.2, rel=0.001)


def test_tubo_peso_fica_entre_o_bastao_cheio_e_zero():
    # Tubo com diâmetro externo 4cm e interno 2cm pesa menos que um bastão cheio de
    # 4cm e mais que um de 2cm, no mesmo comprimento e material.
    peso_tubo = peso_kg("tubo", 1.0, height_cm=2, width_cm=4, length_cm=100)
    peso_bastao_grande = peso_kg("bastao_redondo", 1.0, height_cm=0, width_cm=4, length_cm=100)
    peso_bastao_pequeno = peso_kg("bastao_redondo", 1.0, height_cm=0, width_cm=2, length_cm=100)

    assert peso_bastao_pequeno < peso_tubo < peso_bastao_grande


def test_dimensao_faltando_conta_como_zero_em_vez_de_quebrar():
    peso = peso_kg("bastao_redondo", DENSIDADE_NY6, height_cm=None, width_cm=None, length_cm=100)

    assert peso == 0.0


def test_formato_desconhecido_levanta_erro():
    with pytest.raises(ValueError):
        peso_kg("hexagono", DENSIDADE_NY6, height_cm=1, width_cm=1, length_cm=100)
