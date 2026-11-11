"""Gera respostas FICTÍCIAS, no mesmo formato bagunçado da exportação do formulário.

Nada aqui vem de respondentes reais: setores, tamanhos e tendências foram inventados.
Os defeitos (espaços sobrando, espaço não separável, resposta em branco, coluna de
e-mail, codificações diferentes) são plantados de propósito, para a limpeza ter o que
limpar.
"""

from __future__ import annotations

import csv
import io
import random
from pathlib import Path

from jss.limpeza import ESCALA_CONCORDANCIA, ESCALA_FREQUENCIA

#: Perguntas de pontuação invertida (ver docs/METODO.md): a tendência entra com sinal trocado.
INVERTIDAS = (4, 9)

SEMENTE = 20261111
NBSP = " "

# setor: (respondentes, tendência de demanda, de controle, de apoio)
UNIDADE_1 = {
    "Produção ": (30, 0.5, -0.3, 0.3),
    "Manutenção": (18, 0.2, 0.3, 0.5),
    "Logística ": (12, 0.3, -0.1, 0.4),
    "Qualidade ": (9, 0.0, 0.4, 0.6),
    "Administrativo": (6, -0.2, 0.6, 0.7),
    "Compras": (3, 0.0, 0.5, 0.5),
    "Segurança": (2, 0.1, 0.4, 0.6),
}
UNIDADE_2 = {
    "Produção ": (27, 0.6, -0.5, 0.6),
    "Manutenção": (10, 0.3, 0.2, 0.7),
    "Expedição": (8, 0.4, -0.2, 0.5),
    "Administrativo": (3, -0.1, 0.5, 0.8),
    "Qualidade ": (2, 0.0, 0.4, 0.7),
}

# (primeira pergunta, última pergunta, escala) de cada bloco do questionário
BLOCOS = ((1, 5, ESCALA_FREQUENCIA), (6, 11, ESCALA_FREQUENCIA), (12, 17, ESCALA_CONCORDANCIA))


def _cabecalho(com_email: bool) -> list[str]:
    itens = [f"Item {i:02d}" for i in range(1, 18)]
    itens[1] = NBSP + itens[1]  # espaço não separável no começo
    itens[11] = itens[11] + NBSP  # e no fim
    pessoais = ["ID", "Hora de início", "Hora de conclusão"] + (["Email"] if com_email else [])
    return pessoais + ["Em qual setor você trabalha"] + itens


def _resposta(rng: random.Random, tendencia: float, pessoa: float, escala, invertida: bool) -> str:
    z = tendencia + 0.7 * pessoa + rng.gauss(0, 0.7)
    if invertida:
        z = -z
    indice = 0 if z > 0.6 else 1 if z > -0.4 else 2 if z > -1.2 else 3
    texto = escala[indice]
    sorteio = rng.random()
    if sorteio < 0.10:
        return texto + NBSP
    if sorteio < 0.15:
        return texto + " "
    return texto


def gerar_unidade(rng: random.Random, setores: dict, com_email: bool) -> list[list[str]]:
    pessoas = [(setor, t) for setor, (n, *t) in setores.items() for _ in range(n)]
    rng.shuffle(pessoas)
    linhas = [_cabecalho(com_email)]
    minuto = 0
    for numero, (setor, tendencias) in enumerate(pessoas, start=1):
        minuto += rng.randint(1, 9)
        inicio = f"11/3/26 {7 + minuto // 60}:{minuto % 60:02d}:{rng.randint(0, 59):02d}"
        fim = f"11/3/26 {7 + (minuto + 4) // 60}:{(minuto + 4) % 60:02d}:{rng.randint(0, 59):02d}"
        linha = [str(numero), inicio, fim] + (["anonymous"] if com_email else []) + [setor]
        for (primeira, ultima, escala), tendencia in zip(BLOCOS, tendencias):
            pessoa = rng.gauss(0, 1)
            for numero_da_pergunta in range(primeira, ultima + 1):
                invertida = numero_da_pergunta in INVERTIDAS
                linha.append(_resposta(rng, tendencia, pessoa, escala, invertida))
        linhas.append(linha)
    return linhas


def _para_csv(linhas: list[list[str]], codificacao: str) -> bytes:
    saida = io.StringIO()
    csv.writer(saida, lineterminator="\r\n").writerows(linhas)
    return saida.getvalue().encode(codificacao)


def gerar(semente: int = SEMENTE) -> dict[str, bytes]:
    """Devolve o conteúdo dos dois arquivos, pronto para gravar."""
    rng = random.Random(semente)
    unidade_1 = gerar_unidade(rng, UNIDADE_1, com_email=False)
    unidade_2 = gerar_unidade(rng, UNIDADE_2, com_email=True)
    unidade_2[7][-9] = ""  # uma resposta em branco plantada
    return {
        "unidade_1.csv": _para_csv(unidade_1, "utf-8"),
        "unidade_2.csv": _para_csv(unidade_2, "cp1252"),
    }


def gravar(pasta: str | Path, semente: int = SEMENTE) -> list[Path]:
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    caminhos = []
    for nome, conteudo in gerar(semente).items():
        (pasta / nome).write_bytes(conteudo)
        caminhos.append(pasta / nome)
    return caminhos
