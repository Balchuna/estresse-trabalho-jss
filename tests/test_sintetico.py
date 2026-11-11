"""Os dados fictícios são reprodutíveis, têm os defeitos plantados e saem limpos."""

import re
from pathlib import Path

import pandas as pd

from jss.limpeza import COLUNAS_PERGUNTAS, ESCALA_CONCORDANCIA, ESCALA_FREQUENCIA, limpar
from jss.sintetico import SEMENTE, gerar, gravar

RAIZ = Path(__file__).resolve().parent.parent
NBSP = "\u00a0"


def test_mesma_semente_mesmos_bytes():
    assert gerar(SEMENTE) == gerar(SEMENTE)
    assert gerar(SEMENTE) != gerar(SEMENTE + 1)


def test_arquivos_do_repositorio_batem_com_o_gerador():
    for nome, conteudo in gerar().items():
        assert (RAIZ / "data" / "sintetico" / nome).read_bytes() == conteudo


def test_defeitos_plantados_existem():
    arquivos = gerar()
    u1 = arquivos["unidade_1.csv"].decode("utf-8")
    u2 = arquivos["unidade_2.csv"].decode("cp1252")
    assert "Email" not in u1.splitlines()[0]
    assert "Email" in u2.splitlines()[0]
    assert NBSP + "Item 02" in u1 and "Item 12" + NBSP in u1
    assert "Frequentemente" + NBSP in u1 and "Às vezes ," in u1
    assert "Produção ," in u1
    assert ",," in u2  # resposta em branco
    try:
        arquivos["unidade_2.csv"].decode("utf-8")
        raise AssertionError("a unidade 2 deveria estar em cp1252")
    except UnicodeDecodeError:
        pass


def test_limpeza_dos_ficticios(tmp_path):
    u1, u2 = gravar(tmp_path)
    dados, qualidade = limpar(u1, u2)

    assert qualidade["Unidade 1"]["respondentes"] == 80
    assert qualidade["Unidade 2"]["respondentes"] == 50
    assert qualidade["Unidade 1"]["colunas_pessoais_removidas"] == 3
    assert qualidade["Unidade 2"]["colunas_pessoais_removidas"] == 4
    assert qualidade["Unidade 2"]["respostas_vazias"] == 1
    assert qualidade["respondentes_em_outros"] == 10
    assert qualidade["unidades_com_outros_abaixo_do_minimo"] == []

    assert list(dados.columns) == ["unidade", "setor"] + COLUNAS_PERGUNTAS
    assert dados.groupby(["unidade", "setor"]).size().min() >= 5
    assert int(dados[COLUNAS_PERGUNTAS].isna().sum().sum()) == 1
    assert set(dados[COLUNAS_PERGUNTAS[:11]].stack().dropna()) == set(ESCALA_FREQUENCIA)
    assert set(dados[COLUNAS_PERGUNTAS[11:]].stack().dropna()) == set(ESCALA_CONCORDANCIA)

    texto = dados.to_csv(index=False)
    assert NBSP not in texto and " ," not in texto
    assert "anonymous" not in texto
    assert not re.search(r"\d+:\d\d:\d\d", texto)  # nenhum horário


def test_saida_do_repositorio_bate_com_a_limpeza(tmp_path):
    u1, u2 = gravar(tmp_path)
    dados, _ = limpar(u1, u2)
    dados.to_csv(tmp_path / "limpo.csv", index=False, encoding="utf-8", lineterminator="\n")
    publicado = pd.read_csv(RAIZ / "data" / "limpo" / "respostas_limpas.csv", dtype=str)
    pd.testing.assert_frame_equal(pd.read_csv(tmp_path / "limpo.csv", dtype=str), publicado)
