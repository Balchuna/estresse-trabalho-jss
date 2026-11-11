"""Roda a análise (fase 3) e grava tabelas, resumo e gráficos.

Sem argumentos: lê data/limpo/ (dados fictícios) e grava em resultados/.
Com --privado: lê data/privado/limpo/ e grava em data/privado/resultados/ (fora do git).
"""

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

import pandas as pd  # noqa: E402

from jss import graficos  # noqa: E402
from jss.analise import analisar  # noqa: E402

TABELAS = ("alfas", "geral", "por_unidade", "por_setor", "comparacao")
CRUZADAS = ("quadrantes_por_unidade", "quadrantes_por_setor", "apoio_por_unidade")


def pastas(privado: bool) -> tuple[Path, Path]:
    base = RAIZ / "data" / "privado" if privado else RAIZ
    return (base / "limpo" if privado else RAIZ / "data" / "limpo"), base / "resultados"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--privado", action="store_true")
    args = parser.parse_args()
    entrada, saida = pastas(args.privado)

    dados = pd.read_csv(entrada / "respostas_limpas.csv", dtype=str)
    r = analisar(dados)

    (saida / "figuras").mkdir(parents=True, exist_ok=True)
    for nome in TABELAS:
        r[nome].round(4).to_csv(saida / f"{nome}.csv", index=False, lineterminator="\n")
    for nome in CRUZADAS:
        r[nome].to_csv(saida / f"{nome}.csv", lineterminator="\n")

    classificado = r["classificado"]
    resumo = {
        "respondentes": len(classificado),
        "com_quadrante": int(classificado["quadrante"].notna().sum()),
        "cortes_mediana": r["cortes"],
        "quadrantes_geral": classificado["quadrante"].value_counts().to_dict(),
        "apoio_geral": classificado["apoio_nivel"].value_counts().to_dict(),
    }
    texto = json.dumps(resumo, ensure_ascii=False, indent=2) + "\n"
    (saida / "resumo.json").write_text(texto, encoding="utf-8", newline="\n")

    nota = "" if args.privado else " Dados sintéticos."
    graficos.escores_por_setor(r["por_setor"], r["cortes"], saida / "figuras" / "escores_por_setor.png", nota)
    graficos.quadrantes_por_setor(r["quadrantes_por_setor"], saida / "figuras" / "quadrantes_por_setor.png", nota)
    print(texto)
    for nome in ("alfas", "por_unidade", "comparacao"):
        print(r[nome].round(3).to_string(index=False), "\n")
