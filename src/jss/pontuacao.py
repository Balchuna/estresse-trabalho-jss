"""Pontuação da versão resumida da Job Stress Scale (fase 2).

Fontes (detalhes em docs/METODO.md):
- itens e dimensões: Alves et al., Rev Saúde Pública 2004;38(2):164-171, Tabela 3;
- pontos de cada resposta, itens invertidos e soma: Aguiar, Fonseca e Valente,
  Rev Bras Epidemiol 2010;13(2):212-222.
"""

from __future__ import annotations

import pandas as pd

from jss.limpeza import COLUNAS_PERGUNTAS, ESCALA_CONCORDANCIA, ESCALA_FREQUENCIA

DIMENSOES = {
    "demanda": COLUNAS_PERGUNTAS[0:5],  # q01 a q05
    "controle": COLUNAS_PERGUNTAS[5:11],  # q06 a q11
    "apoio": COLUNAS_PERGUNTAS[11:17],  # q12 a q17
}
#: Subdimensões do controle (Alves et al., 2004).
SUBDIMENSOES_CONTROLE = {
    "discernimento": COLUNAS_PERGUNTAS[5:9],  # q06 a q09
    "autoridade": COLUNAS_PERGUNTAS[9:11],  # q10 e q11
}
#: q04 = "tempo suficiente" (demanda); q09 = "repetir as mesmas tarefas" (controle).
ITENS_INVERTIDOS = ("q04", "q09")
FAIXAS = {"demanda": (5, 20), "controle": (6, 24), "apoio": (6, 24)}

# A primeira opção de cada escala vale 4 e a última vale 1.
_PONTOS = {
    **{texto: 4 - i for i, texto in enumerate(ESCALA_FREQUENCIA)},
    **{texto: 4 - i for i, texto in enumerate(ESCALA_CONCORDANCIA)},
}


def pontuar_itens(dados: pd.DataFrame) -> pd.DataFrame:
    """Troca cada resposta por 1 a 4, já invertendo q04 e q09. Ausente continua ausente."""
    pontos = dados[COLUNAS_PERGUNTAS].apply(lambda coluna: coluna.map(_PONTOS)).astype("float")
    for item in ITENS_INVERTIDOS:
        pontos[item] = 5 - pontos[item]
    return pontos


def calcular_escores(dados: pd.DataFrame) -> pd.DataFrame:
    """Devolve unidade, setor e o escore (soma dos itens) de cada dimensão.

    Quem deixou algum item da dimensão sem resposta fica sem escore nessa dimensão:
    nada é preenchido por estimativa.
    """
    pontos = pontuar_itens(dados)
    escores = dados[["unidade", "setor"]].copy()
    for dimensao, itens in DIMENSOES.items():
        escores[dimensao] = pontos[itens].sum(axis=1, skipna=False)
    return escores
