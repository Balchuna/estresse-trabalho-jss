"""Gráficos de barras da análise. Sem pizza e sem nenhuma coluna de horário."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from jss.analise import QUADRANTES  # noqa: E402
from jss.pontuacao import FAIXAS  # noqa: E402

# Paleta Okabe-Ito, legível para daltônicos.
CORES_UNIDADE = {"Unidade 1": "#0072B2", "Unidade 2": "#E69F00"}
CORES_QUADRANTE = {
    "Alta exigência": "#D55E00",
    "Trabalho ativo": "#E69F00",
    "Trabalho passivo": "#56B4E9",
    "Baixa exigência": "#009E73",
}
NOMES = {"demanda": "Demanda", "controle": "Controle", "apoio": "Apoio social"}


def _rotulos(tabela: pd.DataFrame) -> list[str]:
    return [f"{u} · {s} (n={n})" for u, s, n in zip(tabela["unidade"], tabela["setor"], tabela["n"])]


def escores_por_setor(por_setor: pd.DataFrame, cortes: dict, caminho: Path, nota: str = "") -> None:
    tabela = por_setor.iloc[::-1]
    fig, eixos = plt.subplots(1, 3, figsize=(13, 0.45 * len(tabela) + 1.8), sharey=True)
    for eixo, dimensao in zip(eixos, NOMES):
        cores = [CORES_UNIDADE[u] for u in tabela["unidade"]]
        barras = eixo.barh(_rotulos(tabela), tabela[f"{dimensao}_media"], color=cores)
        eixo.bar_label(barras, fmt="%.1f", padding=3, fontsize=8,
                       bbox={"facecolor": "white", "edgecolor": "none", "pad": 1})
        eixo.axvline(cortes[dimensao], color="#444444", linestyle="--", linewidth=1, zorder=0)
        eixo.set_xlim(FAIXAS[dimensao][0], FAIXAS[dimensao][1])
        eixo.set_title(f"{NOMES[dimensao]} (média, de {FAIXAS[dimensao][0]} a {FAIXAS[dimensao][1]})", fontsize=10)
        eixo.spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"Escore médio por setor. Linha tracejada: mediana geral (corte).{nota}", fontsize=11)
    fig.tight_layout()
    fig.savefig(caminho, dpi=130)
    plt.close(fig)


def quadrantes_por_setor(contagens: pd.DataFrame, caminho: Path, nota: str = "") -> None:
    """Barras empilhadas em 100%: fatia de cada quadrante em cada grupo."""
    totais = contagens.sum(axis=1)
    pct = contagens.div(totais, axis=0).mul(100).iloc[::-1]
    rotulos = [f"{u} · {s} (n={totais[(u, s)]})" for u, s in pct.index]
    fig, eixo = plt.subplots(figsize=(10, 0.45 * len(pct) + 1.8))
    esquerda = pd.Series(0.0, index=pct.index)
    for quadrante in QUADRANTES:
        barras = eixo.barh(rotulos, pct[quadrante], left=esquerda.values,
                           color=CORES_QUADRANTE[quadrante], label=quadrante)
        textos = [f"{v:.0f}%" if v >= 8 else "" for v in pct[quadrante]]
        eixo.bar_label(barras, labels=textos, label_type="center", fontsize=8, color="white")
        esquerda += pct[quadrante]
    eixo.set_xlim(0, 100)
    eixo.set_xlabel("% dos respondentes do grupo")
    eixo.spines[["top", "right"]].set_visible(False)
    eixo.legend(ncol=4, loc="lower center", bbox_to_anchor=(0.5, 1.0), frameon=False, fontsize=9)
    fig.suptitle(f"Quadrantes do modelo demanda-controle por setor.{nota}", fontsize=11, y=0.99)
    fig.tight_layout()
    fig.savefig(caminho, dpi=130)
    plt.close(fig)
