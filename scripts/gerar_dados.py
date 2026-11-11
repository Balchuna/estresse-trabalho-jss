"""Gera os dois CSV fictícios em data/sintetico/. Uso: python scripts/gerar_dados.py"""

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from jss.sintetico import SEMENTE, gravar  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", default=str(RAIZ / "data" / "sintetico"))
    parser.add_argument("--semente", type=int, default=SEMENTE)
    args = parser.parse_args()
    for caminho in gravar(args.saida, args.semente):
        print("gravado:", caminho.name)
