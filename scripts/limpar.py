"""Roda a limpeza (fase 1).

Sem argumentos, limpa os dados fictícios de data/sintetico/ e grava em data/limpo/.

Com --entrada PASTA (que deve ter unidade_1.csv e unidade_2.csv), a saída padrão é
data/privado/limpo/, que o git ignora. É o caminho para dados reais, que nunca são
publicados.
"""

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from jss.limpeza import MINIMO_POR_SETOR, limpar  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada")
    parser.add_argument("--saida")
    parser.add_argument("--minimo", type=int, default=MINIMO_POR_SETOR)
    args = parser.parse_args()

    entrada = Path(args.entrada) if args.entrada else RAIZ / "data" / "sintetico"
    padrao = RAIZ / "data" / ("privado/limpo" if args.entrada else "limpo")
    saida = Path(args.saida) if args.saida else padrao

    dados, qualidade = limpar(
        entrada / "unidade_1.csv", entrada / "unidade_2.csv", minimo=args.minimo
    )
    saida.mkdir(parents=True, exist_ok=True)
    dados.to_csv(saida / "respostas_limpas.csv", index=False, encoding="utf-8", lineterminator="\n")
    texto = json.dumps(qualidade, ensure_ascii=False, indent=2) + "\n"
    (saida / "qualidade.json").write_text(texto, encoding="utf-8", newline="\n")
    print(texto)
    print(dados.groupby(["unidade", "setor"]).size().to_string())
