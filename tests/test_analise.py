from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from jss.analise import (
    alfa_de_cronbach,
    analisar,
    calcular_cortes,
    classificar,
    comparar_unidades,
    descritivo,
)

RAIZ = Path(__file__).resolve().parent.parent


def escores(linhas):
    return pd.DataFrame(linhas, columns=["unidade", "setor", "demanda", "controle", "apoio"])


def test_corte_e_a_mediana_geral():
    e = escores([("Unidade 1", "A", d, c, a) for d, c, a in [(10, 12, 20), (12, 14, 22), (20, 6, 6)]])
    assert calcular_cortes(e) == {"demanda": 12.0, "controle": 12.0, "apoio": 20.0}


def test_quatro_quadrantes_e_empate_conta_como_baixo():
    cortes = {"demanda": 12, "controle": 15, "apoio": 18}
    e = escores([
        ("Unidade 1", "A", 13, 15, 19),  # demanda alta, controle igual ao corte = baixo
        ("Unidade 1", "A", 13, 16, 18),  # alta e alto; apoio igual ao corte = baixo
        ("Unidade 1", "A", 12, 15, 10),  # baixa e baixo
        ("Unidade 1", "A", 12, 16, 24),  # baixa e alto
        ("Unidade 1", "A", np.nan, 16, np.nan),
    ])
    c = classificar(e, cortes)
    assert list(c["quadrante"][:4]) == ["Alta exigência", "Trabalho ativo", "Trabalho passivo", "Baixa exigência"]
    assert pd.isna(c.loc[4, "quadrante"]) and pd.isna(c.loc[4, "apoio_nivel"])
    assert list(c["apoio_nivel"][:4]) == ["Alto apoio", "Baixo apoio", "Baixo apoio", "Alto apoio"]


def test_alfa_de_cronbach_caso_calculado_a_mao():
    # Variâncias dos itens: 1, 1 e 1. Somas: 3, 6, 9 -> variância 9. alfa = 3/2 * (1 - 3/9) = 1.
    iguais = pd.DataFrame({"a": [1, 2, 3], "b": [1, 2, 3], "c": [1, 2, 3]})
    assert alfa_de_cronbach(iguais) == pytest.approx(1.0)
    # Itens: var 1 e 1; somas 4, 4, 4 -> variância 0 -> alfa = 2 * (1 - 2/0) não existe;
    # caso com números fechados: somas 2, 5, 5 -> var 3; alfa = 2 * (1 - 2/3) = 0.6667.
    misto = pd.DataFrame({"a": [1, 2, 3], "b": [1, 3, 2]})
    assert alfa_de_cronbach(misto) == pytest.approx(2 / 3)


def test_alfa_ignora_quem_tem_item_ausente():
    itens = pd.DataFrame({"a": [1, 2, 3, 4], "b": [1, 3, 2, None]})
    assert alfa_de_cronbach(itens) == pytest.approx(2 / 3)


def test_comparacao_efeito_vai_de_menos_1_a_1_com_sinal_certo():
    e = escores([("Unidade 1", "A", 20, 10, 15)] * 5 + [("Unidade 2", "A", 10, 20, 15)] * 5)
    c = comparar_unidades(e).set_index("dimensao")
    assert c.loc["demanda", "efeito_r"] == pytest.approx(1.0)   # Unidade 1 sempre maior
    assert c.loc["controle", "efeito_r"] == pytest.approx(-1.0)
    assert c.loc["apoio", "efeito_r"] == pytest.approx(0.0)
    assert c.loc["demanda", "p"] < 0.05


def test_descritivo_recusa_grupo_com_menos_de_5():
    e = escores([("Unidade 1", "A", 10, 10, 10)] * 5 + [("Unidade 1", "B", 10, 10, 10)] * 4)
    c = classificar(e, calcular_cortes(e))
    with pytest.raises(ValueError, match="menos de 5"):
        descritivo(c, ["unidade", "setor"])


def test_analise_dos_ficticios_fecha_as_contas():
    dados = pd.read_csv(RAIZ / "data" / "limpo" / "respostas_limpas.csv", dtype=str)
    r = analisar(dados)
    c = r["classificado"]
    assert len(c) == 130
    assert r["por_unidade"]["n"].tolist() == [80, 50]
    assert r["por_setor"]["n"].sum() == 130 and r["por_setor"]["n"].min() >= 5
    assert r["quadrantes_por_setor"].to_numpy().sum() == c["quadrante"].notna().sum() == 129
    for dimensao, (menor, maior) in {"demanda": (5, 20), "controle": (6, 24), "apoio": (6, 24)}.items():
        assert c[dimensao].dropna().between(menor, maior).all()
    assert (r["alfas"]["alfa"] < 1).all()


def test_resultados_do_repositorio_batem_com_a_analise():
    dados = pd.read_csv(RAIZ / "data" / "limpo" / "respostas_limpas.csv", dtype=str)
    r = analisar(dados)
    for nome in ("alfas", "por_unidade", "por_setor", "comparacao"):
        publicado = pd.read_csv(RAIZ / "resultados" / f"{nome}.csv")
        numeros = publicado.select_dtypes("number").columns
        np.testing.assert_allclose(publicado[numeros], r[nome][numeros], atol=1e-4)
