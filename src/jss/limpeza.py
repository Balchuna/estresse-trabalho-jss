"""Limpeza e anonimização das respostas do questionário (fase 1).

Entrada: dois CSV exportados do formulário, um por unidade.
Saída: uma tabela só, com as colunas `unidade`, `setor` e `q01` a `q17`.

Regras de anonimização aplicadas aqui:
- colunas pessoais (ID, horários, e-mail, nome) nem chegam a ser carregadas na tabela;
- o texto das perguntas não sai daqui: as colunas viram `q01`..`q17`, pela posição;
- setores com menos de 5 respondentes na unidade viram "Outros";
- a ordem das linhas é embaralhada, porque a ordem original segue o horário da resposta.
"""

from __future__ import annotations

import csv
import io
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

N_PERGUNTAS = 17
#: As 11 primeiras perguntas usam a escala de frequência; as 6 últimas, a de concordância.
N_FREQUENCIA = 11
ESCALA_FREQUENCIA = ("Frequentemente", "Às vezes", "Raramente", "Nunca ou quase nunca")
ESCALA_CONCORDANCIA = (
    "Concordo totalmente",
    "Concordo mais que discordo",
    "Discordo mais que concordo",
    "Discordo",
)
COLUNAS_PERGUNTAS = [f"q{i:02d}" for i in range(1, N_PERGUNTAS + 1)]
MINIMO_POR_SETOR = 5
SETOR_OUTROS = "Outros"
SETOR_VAZIO = "Não informado"
SEMENTE_EMBARALHAR = 20261111

_COLUNAS_PESSOAIS = {"id", "email", "e-mail", "nome"}


def normalizar_texto(valor: str) -> str:
    """Troca espaço não separável por espaço comum e tira espaços sobrando."""
    return " ".join(str(valor).replace(" ", " ").split())


def _chave(valor: str) -> str:
    """Forma de comparação: sem acento, sem caixa, sem espaço sobrando."""
    sem_acento = unicodedata.normalize("NFKD", normalizar_texto(valor))
    return "".join(c for c in sem_acento if not unicodedata.combining(c)).casefold()


def eh_coluna_pessoal(nome: str) -> bool:
    chave = _chave(nome)
    return chave in _COLUNAS_PESSOAIS or chave.startswith("hora de ")


def escala_da_pergunta(coluna: str) -> tuple[str, ...]:
    numero = int(coluna[1:])
    return ESCALA_FREQUENCIA if numero <= N_FREQUENCIA else ESCALA_CONCORDANCIA


def decodificar(bruto: bytes) -> tuple[str, str]:
    """Tenta UTF-8 (com ou sem BOM); se falhar, usa cp1252."""
    try:
        return bruto.decode("utf-8-sig"), "utf-8"
    except UnicodeDecodeError:
        return bruto.decode("cp1252"), "cp1252"


def ler_sem_dados_pessoais(caminho: str | Path) -> tuple[pd.DataFrame, dict]:
    """Lê o CSV já sem as colunas pessoais. Tudo vem como texto."""
    texto, codificacao = decodificar(Path(caminho).read_bytes())
    primeira_linha = texto.split("\n", 1)[0]
    separador = ";" if primeira_linha.count(";") > primeira_linha.count(",") else ","
    cabecalho = next(csv.reader(io.StringIO(texto), delimiter=separador))
    tabela = pd.read_csv(
        io.StringIO(texto),
        sep=separador,
        dtype=str,
        keep_default_na=False,
        usecols=lambda nome: not eh_coluna_pessoal(nome),
    )
    info = {
        "codificacao": codificacao,
        "colunas_pessoais_removidas": len(cabecalho) - len(tabela.columns),
    }
    return tabela, info


@dataclass
class UnidadeLimpa:
    dados: pd.DataFrame
    #: Texto normalizado das 17 perguntas. Fica só na memória, para comparar as unidades.
    perguntas: list[str]
    qualidade: dict


def limpar_unidade(caminho: str | Path, unidade: str) -> UnidadeLimpa:
    tabela, info = ler_sem_dados_pessoais(caminho)
    tabela.columns = [normalizar_texto(c) for c in tabela.columns]

    colunas_setor = [c for c in tabela.columns if "setor" in _chave(c)]
    if len(colunas_setor) != 1:
        raise ValueError(
            f"{unidade}: esperava 1 coluna de setor, achei {len(colunas_setor)}."
        )
    perguntas = [c for c in tabela.columns if c != colunas_setor[0]]
    if len(perguntas) != N_PERGUNTAS:
        raise ValueError(
            f"{unidade}: esperava {N_PERGUNTAS} perguntas, achei {len(perguntas)}."
        )

    tabela = tabela.map(normalizar_texto)
    tabela = tabela[(tabela != "").any(axis=1)]

    dados = pd.DataFrame({"unidade": unidade}, index=tabela.index)
    dados["setor"] = tabela[colunas_setor[0]].replace("", SETOR_VAZIO)

    vazias = 0
    fora_da_escala = 0
    for coluna, pergunta in zip(COLUNAS_PERGUNTAS, perguntas):
        validos = {_chave(v): v for v in escala_da_pergunta(coluna)}
        chaves = tabela[pergunta].map(_chave)
        vazias += int((chaves == "").sum())
        fora_da_escala += int(((chaves != "") & ~chaves.isin(list(validos))).sum())
        dados[coluna] = chaves.map(validos)  # vazio ou fora da escala vira ausente

    qualidade = {
        **info,
        "respondentes": len(dados),
        "respostas_vazias": vazias,
        "respostas_fora_da_escala": fora_da_escala,
    }
    return UnidadeLimpa(dados.reset_index(drop=True), perguntas, qualidade)


def validar_mesmas_perguntas(perguntas_1: list[str], perguntas_2: list[str]) -> None:
    """Falha se as unidades não tiverem as mesmas perguntas, na mesma ordem.

    A mensagem cita só as posições, nunca o texto das perguntas.
    """
    diferentes = [
        i
        for i, (a, b) in enumerate(zip(perguntas_1, perguntas_2), start=1)
        if _chave(a) != _chave(b)
    ]
    if len(perguntas_1) != len(perguntas_2) or diferentes:
        raise ValueError(
            "As unidades não têm as mesmas perguntas. "
            f"Posições diferentes: {diferentes or 'quantidade diferente'}."
        )


def agrupar_setores_pequenos(
    dados: pd.DataFrame, minimo: int = MINIMO_POR_SETOR
) -> tuple[pd.DataFrame, dict]:
    """Em cada unidade, setor com menos de `minimo` respondentes vira "Outros"."""
    dados = dados.copy()
    tamanho = dados.groupby(["unidade", "setor"])["setor"].transform("size")
    pequenos = tamanho < minimo
    resumo = {
        "setores_agrupados_em_outros": int(
            dados.loc[pequenos, ["unidade", "setor"]].drop_duplicates().shape[0]
        ),
        "respondentes_em_outros": int(pequenos.sum()),
    }
    dados.loc[pequenos, "setor"] = SETOR_OUTROS
    outros = dados[dados["setor"] == SETOR_OUTROS].groupby("unidade").size()
    # Se sobrar um "Outros" menor que o mínimo, a análise não pode mostrá-lo separado.
    resumo["unidades_com_outros_abaixo_do_minimo"] = sorted(
        outros[outros < minimo].index
    )
    return dados, resumo


def limpar(
    caminho_unidade_1: str | Path,
    caminho_unidade_2: str | Path,
    minimo: int = MINIMO_POR_SETOR,
    semente: int = SEMENTE_EMBARALHAR,
) -> tuple[pd.DataFrame, dict]:
    """Roda a fase 1 inteira e devolve a tabela limpa e o resumo de qualidade."""
    u1 = limpar_unidade(caminho_unidade_1, "Unidade 1")
    u2 = limpar_unidade(caminho_unidade_2, "Unidade 2")
    validar_mesmas_perguntas(u1.perguntas, u2.perguntas)

    dados = pd.concat([u1.dados, u2.dados], ignore_index=True)
    dados, resumo_setores = agrupar_setores_pequenos(dados, minimo)
    dados = dados.sample(frac=1, random_state=semente).reset_index(drop=True)

    qualidade = {
        "Unidade 1": u1.qualidade,
        "Unidade 2": u2.qualidade,
        "mesmas_17_perguntas": True,
        "minimo_por_setor": minimo,
        **resumo_setores,
        "total_de_respondentes": len(dados),
    }
    return dados, qualidade
