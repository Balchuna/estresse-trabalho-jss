"""Análise dos escores (fase 3): quadrantes, apoio, alfa de Cronbach, descritivos
e comparação entre as unidades."""

from __future__ import annotations

import pandas as pd
from scipy.stats import mannwhitneyu

from jss.limpeza import MINIMO_POR_SETOR
from jss.pontuacao import DIMENSOES, SUBDIMENSOES_CONTROLE, calcular_escores, pontuar_itens

QUADRANTES = ("Alta exigência", "Trabalho ativo", "Trabalho passivo", "Baixa exigência")


def calcular_cortes(escores: pd.DataFrame) -> dict[str, float]:
    """Corte de cada dimensão: a mediana de todos os respondentes juntos."""
    return {d: float(escores[d].median()) for d in DIMENSOES}


def classificar(escores: pd.DataFrame, cortes: dict[str, float]) -> pd.DataFrame:
    """Acrescenta `quadrante` (demanda x controle) e `apoio_nivel`.

    "Alto" é estar ACIMA da mediana; igual à mediana conta como "baixo".
    Quem não tem escore de demanda ou de controle fica sem quadrante.
    """
    saida = escores.copy()
    alta_demanda = saida["demanda"] > cortes["demanda"]
    alto_controle = saida["controle"] > cortes["controle"]
    saida["quadrante"] = "Baixa exigência"
    saida.loc[alta_demanda & ~alto_controle, "quadrante"] = "Alta exigência"
    saida.loc[alta_demanda & alto_controle, "quadrante"] = "Trabalho ativo"
    saida.loc[~alta_demanda & ~alto_controle, "quadrante"] = "Trabalho passivo"
    saida.loc[saida[["demanda", "controle"]].isna().any(axis=1), "quadrante"] = pd.NA

    saida["apoio_nivel"] = "Baixo apoio"
    saida.loc[saida["apoio"] > cortes["apoio"], "apoio_nivel"] = "Alto apoio"
    saida.loc[saida["apoio"].isna(), "apoio_nivel"] = pd.NA
    return saida


def alfa_de_cronbach(itens: pd.DataFrame) -> float:
    """Consistência interna, só com quem respondeu todos os itens.

    alfa = k/(k-1) * (1 - soma das variâncias dos itens / variância da soma)
    """
    completos = itens.dropna()
    k = completos.shape[1]
    variancia_dos_itens = completos.var(ddof=1).sum()
    variancia_da_soma = completos.sum(axis=1).var(ddof=1)
    return float(k / (k - 1) * (1 - variancia_dos_itens / variancia_da_soma))


def tabela_de_alfas(dados: pd.DataFrame) -> pd.DataFrame:
    pontos = pontuar_itens(dados)
    grupos = {**DIMENSOES, **{f"controle: {n}": i for n, i in SUBDIMENSOES_CONTROLE.items()}}
    linhas = [
        {"dimensao": nome, "itens": len(itens), "n": len(pontos[itens].dropna()),
         "alfa": alfa_de_cronbach(pontos[itens])}
        for nome, itens in grupos.items()
    ]
    return pd.DataFrame(linhas)


def descritivo(classificado: pd.DataFrame, por: list[str]) -> pd.DataFrame:
    """Uma linha por grupo: n, média, desvio-padrão e mediana de cada dimensão,
    e o percentual de alta exigência e de baixo apoio."""
    linhas = []
    for chave, grupo in classificado.groupby(por):
        chave = chave if isinstance(chave, tuple) else (chave,)
        linha = dict(zip(por, chave)) | {"n": len(grupo)}
        for d in DIMENSOES:
            linha[f"{d}_media"] = grupo[d].mean()
            linha[f"{d}_dp"] = grupo[d].std(ddof=1)
            linha[f"{d}_mediana"] = grupo[d].median()
        linha["pct_alta_exigencia"] = 100 * (grupo["quadrante"] == "Alta exigência").sum() / grupo["quadrante"].notna().sum()
        linha["pct_baixo_apoio"] = 100 * (grupo["apoio_nivel"] == "Baixo apoio").sum() / grupo["apoio_nivel"].notna().sum()
        linhas.append(linha)
    tabela = pd.DataFrame(linhas)
    if (tabela["n"] < MINIMO_POR_SETOR).any():
        raise ValueError("Há grupo com menos de 5 respondentes: não pode ser mostrado.")
    return tabela


def quadrantes_por_grupo(classificado: pd.DataFrame, por: list[str]) -> pd.DataFrame:
    """Contagem de pessoas em cada quadrante, por grupo."""
    tabela = pd.crosstab([classificado[c] for c in por], classificado["quadrante"])
    return tabela.reindex(columns=list(QUADRANTES), fill_value=0)


def comparar_unidades(escores: pd.DataFrame) -> pd.DataFrame:
    """Unidade 1 x Unidade 2 em cada dimensão: Mann-Whitney e tamanho de efeito.

    O efeito é a correlação bisserial por postos: r = 2*U1/(n1*n2) - 1.
    Vai de -1 a 1; positivo quer dizer escores maiores na Unidade 1.
    """
    linhas = []
    for d in DIMENSOES:
        a = escores.loc[escores["unidade"] == "Unidade 1", d].dropna()
        b = escores.loc[escores["unidade"] == "Unidade 2", d].dropna()
        teste = mannwhitneyu(a, b, alternative="two-sided")
        linhas.append({
            "dimensao": d, "n_unidade_1": len(a), "n_unidade_2": len(b),
            "mediana_unidade_1": a.median(), "mediana_unidade_2": b.median(),
            "U": float(teste.statistic), "p": float(teste.pvalue),
            "efeito_r": float(2 * teste.statistic / (len(a) * len(b)) - 1),
        })
    return pd.DataFrame(linhas)


def analisar(dados: pd.DataFrame) -> dict[str, object]:
    """Roda tudo a partir da tabela limpa e devolve as tabelas de resultado."""
    escores = calcular_escores(dados)
    cortes = calcular_cortes(escores)
    classificado = classificar(escores, cortes)
    return {
        "classificado": classificado,
        "cortes": cortes,
        "alfas": tabela_de_alfas(dados),
        "geral": descritivo(classificado.assign(grupo="Todos"), ["grupo"]),
        "por_unidade": descritivo(classificado, ["unidade"]),
        "por_setor": descritivo(classificado, ["unidade", "setor"]),
        "quadrantes_por_unidade": quadrantes_por_grupo(classificado, ["unidade"]),
        "quadrantes_por_setor": quadrantes_por_grupo(classificado, ["unidade", "setor"]),
        "apoio_por_unidade": pd.crosstab(classificado["unidade"], classificado["apoio_nivel"]),
        "comparacao": comparar_unidades(escores),
    }
