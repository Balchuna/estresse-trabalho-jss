import pandas as pd
import pytest

from jss.limpeza import COLUNAS_PERGUNTAS
from jss.pontuacao import DIMENSOES, FAIXAS, ITENS_INVERTIDOS, calcular_escores, pontuar_itens


def pessoa(freq="Frequentemente", conc="Concordo totalmente", **trocas):
    linha = {"unidade": "Unidade 1", "setor": "A"}
    linha |= {q: freq for q in COLUNAS_PERGUNTAS[:11]}
    linha |= {q: conc for q in COLUNAS_PERGUNTAS[11:]}
    return linha | trocas


def tabela(*pessoas):
    return pd.DataFrame(pessoas)


def test_dimensoes_tem_5_6_e_6_itens_sem_repeticao():
    assert [len(v) for v in DIMENSOES.values()] == [5, 6, 6]
    assert sorted(sum(DIMENSOES.values(), [])) == COLUNAS_PERGUNTAS


def test_itens_invertidos_sao_q04_e_q09():
    assert ITENS_INVERTIDOS == ("q04", "q09")
    assert "q04" in DIMENSOES["demanda"] and "q09" in DIMENSOES["controle"]


@pytest.mark.parametrize("resposta, direto, invertido", [
    ("Frequentemente", 4, 1), ("Às vezes", 3, 2), ("Raramente", 2, 3), ("Nunca ou quase nunca", 1, 4)])
def test_pontos_da_escala_de_frequencia(resposta, direto, invertido):
    pontos = pontuar_itens(tabela(pessoa(freq=resposta))).iloc[0]
    assert pontos["q01"] == direto and pontos["q06"] == direto
    assert pontos["q04"] == invertido and pontos["q09"] == invertido


@pytest.mark.parametrize("resposta, pontos_esperados", [
    ("Concordo totalmente", 4), ("Concordo mais que discordo", 3),
    ("Discordo mais que concordo", 2), ("Discordo", 1)])
def test_pontos_da_escala_de_concordancia(resposta, pontos_esperados):
    pontos = pontuar_itens(tabela(pessoa(conc=resposta))).iloc[0]
    assert (pontos[DIMENSOES["apoio"]] == pontos_esperados).all()


def test_quem_responde_sempre_frequentemente_nao_chega_ao_maximo():
    # 4 itens diretos valem 4 e o invertido vale 1: 17 de demanda, e 5*4 + 1 = 21 de controle.
    e = calcular_escores(tabela(pessoa())).iloc[0]
    assert (e["demanda"], e["controle"], e["apoio"]) == (17, 21, 24)


def test_extremos_batem_com_as_faixas():
    maximo = pessoa(q04="Nunca ou quase nunca", q09="Nunca ou quase nunca")
    minimo = pessoa(freq="Nunca ou quase nunca", conc="Discordo",
                    q04="Frequentemente", q09="Frequentemente")
    e = calcular_escores(tabela(maximo, minimo))
    for dimensao, (menor, maior) in FAIXAS.items():
        assert e.loc[0, dimensao] == maior
        assert e.loc[1, dimensao] == menor


def test_caso_calculado_a_mao():
    p = pessoa(q01="Às vezes", q02="Raramente", q03="Frequentemente", q04="Raramente",
               q05="Nunca ou quase nunca",          # 3 + 2 + 4 + (5-2) + 1 = 13
               q06="Às vezes", q07="Às vezes", q08="Raramente", q09="Frequentemente",
               q10="Nunca ou quase nunca", q11="Às vezes",  # 3 + 3 + 2 + (5-4) + 1 + 3 = 13
               q12="Discordo", q13="Concordo mais que discordo")  # 1 + 3 + 4*4 = 20
    e = calcular_escores(tabela(p)).iloc[0]
    assert (e["demanda"], e["controle"], e["apoio"]) == (13, 13, 20)


def test_item_ausente_deixa_so_aquela_dimensao_sem_escore():
    e = calcular_escores(tabela(pessoa(q05=None))).iloc[0]
    assert pd.isna(e["demanda"])
    assert (e["controle"], e["apoio"]) == (21, 24)
