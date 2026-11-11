"""Monta o relatório em HTML (fase 4) a partir das tabelas de resultados.

Sem argumentos: lê resultados/ e grava resultados/relatorio.html.
Com --privado: usa data/privado/resultados/ (fora do git).
A seção "Interpretação" vem de docs/INTERPRETACAO.md, escrita pelo Rafael.
"""

import argparse
import html
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

import pandas as pd  # noqa: E402

NOMES = {"demanda": "Demanda", "controle": "Controle", "apoio": "Apoio social",
         "controle: discernimento": "Controle: discernimento intelectual",
         "controle: autoridade": "Controle: autoridade sobre decisões"}
ESTILO = """
body{font-family:Segoe UI,Arial,sans-serif;max-width:920px;margin:2rem auto;padding:0 1rem;color:#222;line-height:1.5}
h1{font-size:1.6rem} h2{margin-top:2rem;border-bottom:2px solid #0072B2;padding-bottom:.2rem;font-size:1.2rem}
table{border-collapse:collapse;margin:1rem 0;font-size:.9rem} th,td{border:1px solid #ccc;padding:.3rem .6rem;text-align:right}
th{background:#f0f4f8} td:first-child,th:first-child,td.t{text-align:left}
img{max-width:100%} .aviso{background:#fff6dd;border-left:4px solid #E69F00;padding:.6rem 1rem}
.pendente{background:#fde8e8;border-left:4px solid #D55E00;padding:.6rem 1rem}
"""


def n(valor, casas=1) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def tabela(cabecalho: list[str], linhas: list[list[str]]) -> str:
    th = "".join(f"<th>{html.escape(c)}</th>" for c in cabecalho)
    corpo = "".join("<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in l) + "</tr>" for l in linhas)
    return f"<table><tr>{th}</tr>{corpo}</table>"


def descritivo(df: pd.DataFrame, chaves: list[str]) -> str:
    cab = [c.capitalize() for c in chaves] + ["n", "Demanda", "Controle", "Apoio", "% alta exigência", "% baixo apoio"]
    linhas = [
        [l[c] for c in chaves] + [l["n"]]
        + [f"{n(l[f'{d}_media'])} ({n(l[f'{d}_dp'])})" for d in ("demanda", "controle", "apoio")]
        + [n(l["pct_alta_exigencia"], 0), n(l["pct_baixo_apoio"], 0)]
        for _, l in df.iterrows()
    ]
    return tabela(cab, linhas)


def interpretacao() -> str:
    texto = (RAIZ / "docs" / "INTERPRETACAO.md").read_text(encoding="utf-8").strip()
    classe = "pendente" if texto.startswith("[A ESCREVER") else ""
    paragrafos = "".join(f"<p>{html.escape(p.strip())}</p>" for p in texto.split("\n\n"))
    return f'<div class="{classe}">{paragrafos}</div>'


def montar(pasta: Path, sintetico: bool) -> str:
    resumo = json.loads((pasta / "resumo.json").read_text(encoding="utf-8"))
    ler = lambda nome, **k: pd.read_csv(pasta / f"{nome}.csv", **k)  # noqa: E731
    alfas, por_unidade, por_setor, comp = ler("alfas"), ler("por_unidade"), ler("por_setor"), ler("comparacao")
    quad = ler("quadrantes_por_unidade", index_col=0)
    apoio = ler("apoio_por_unidade", index_col=0)

    total = resumo["com_quadrante"]
    q = resumo["quadrantes_geral"]
    pior = por_setor.sort_values("pct_alta_exigencia", ascending=False).iloc[0]
    cortes = resumo["cortes_mediana"]
    aviso = ('<p class="aviso"><strong>Dados sintéticos.</strong> Todas as respostas foram geradas por '
             "computador. Os números mostram o método funcionando e não descrevem nenhuma empresa real.</p>"
             if sintetico else "")

    partes = [
        f"<h1>Estresse no trabalho por setor: Job Stress Scale</h1>{aviso}",
        "<h2>1. Resumo executivo</h2><ul>",
        f"<li>{resumo['respondentes']} respondentes em duas unidades ({por_unidade['n'][0]} e {por_unidade['n'][1]}); "
        f"{total} com escore completo de demanda e controle.</li>",
        f"<li>Alta exigência (demanda alta com controle baixo): {q.get('Alta exigência', 0)} pessoas, "
        f"{n(100 * q.get('Alta exigência', 0) / total, 0)}% dos classificados.</li>",
        f"<li>Grupo com maior proporção de alta exigência: {html.escape(pior['unidade'])}, setor "
        f"{html.escape(pior['setor'])} ({n(pior['pct_alta_exigencia'], 0)}% de {pior['n']} pessoas).</li>",
        "<li>Diferença entre as unidades: ver a seção 3.4, com teste e tamanho de efeito.</li></ul>",

        "<h2>2. Método</h2>",
        "<p>Instrumento: versão resumida da Job Stress Scale adaptada para o português (Alves et al., 2004), "
        "com 17 perguntas: 5 de demanda, 6 de controle e 6 de apoio social. Cada resposta vale de 1 a 4; "
        "dois itens são invertidos; o escore de cada dimensão é a soma dos itens (demanda de 5 a 20; controle "
        "e apoio de 6 a 24). Regras de pontuação conforme Aguiar et al. (2010).</p>",
        f"<p>Corte para “alto”: escore acima da mediana de todos os respondentes (demanda {n(cortes['demanda'], 1)}; "
        f"controle {n(cortes['controle'], 1)}; apoio {n(cortes['apoio'], 1)}). Setores com menos de 5 respondentes "
        "foram agrupados em “Outros”. Comparação entre unidades: teste de Mann-Whitney e correlação bisserial "
        "por postos.</p>",

        "<h2>3. Resultados</h2><h3>3.1 Consistência interna</h3>",
        tabela(["Dimensão", "Itens", "n", "Alfa de Cronbach"],
               [[NOMES[l["dimensao"]], l["itens"], l["n"], n(l["alfa"], 2)] for _, l in alfas.iterrows()]),
        "<h3>3.2 Escores por unidade e por setor</h3><p>Média (desvio-padrão) de cada dimensão.</p>",
        descritivo(por_unidade, ["unidade"]), descritivo(por_setor, ["unidade", "setor"]),
        '<img src="figuras/escores_por_setor.png" alt="Barras: escore médio de demanda, controle e apoio por setor">',
        "<h3>3.3 Quadrantes do modelo demanda-controle</h3>",
        tabela(["Unidade"] + list(quad.columns), [[i] + list(l) for i, l in quad.iterrows()]),
        '<img src="figuras/quadrantes_por_setor.png" alt="Barras empilhadas: quadrantes por setor">',
        "<p>Apoio social:</p>",
        tabela(["Unidade"] + list(apoio.columns), [[i] + list(l) for i, l in apoio.iterrows()]),
        "<h3>3.4 Comparação entre as unidades</h3>",
        tabela(["Dimensão", "Mediana U1", "Mediana U2", "U", "p", "Efeito r"],
               [[NOMES[l["dimensao"]], n(l["mediana_unidade_1"]), n(l["mediana_unidade_2"]), n(l["U"]),
                 n(l["p"], 3), n(l["efeito_r"], 2)] for _, l in comp.iterrows()]),
        "<p>O efeito r vai de −1 a 1; positivo indica escores maiores na Unidade 1. Com amostras deste tamanho, "
        "o teste só detecta diferenças grandes: um p alto não prova que as unidades são iguais.</p>",

        "<h2>4. Interpretação</h2>", interpretacao(),

        "<h2>5. Limitações</h2><ul>",
        "<li><strong>Autorrelato:</strong> mede a percepção de quem respondeu, sujeita ao humor do dia e ao receio de se expor.</li>",
        "<li><strong>Recorte transversal:</strong> é uma foto de um momento; não mostra causa nem evolução.</li>",
        "<li><strong>Amostra pequena:</strong> em setores com poucos respondentes, uma ou duas pessoas mudam o resultado.</li>",
        "<li><strong>Rastreamento, não diagnóstico:</strong> a escala aponta onde olhar; não diagnostica pessoas nem adoecimento.</li>",
        "<li><strong>Corte pela mediana:</strong> “alto” e “baixo” são relativos a este grupo, não a uma norma externa.</li>",
        "<li><strong>Consistência interna:</strong> dimensões com alfa baixo devem ser lidas com mais cautela.</li></ul>",

        "<h2>6. Uso possível na gestão de riscos psicossociais (PGR)</h2><ul>",
        "<li>Entrar no inventário de riscos do PGR como evidência de triagem dos fatores psicossociais ligados à organização do trabalho.</li>",
        "<li>Priorizar setores para avaliação aprofundada (entrevistas, observação da atividade) antes de definir medidas.</li>",
        "<li>Servir de linha de base: repetir a aplicação depois das medidas e comparar os escores por setor.</li>",
        "<li>Divulgar só resultados agregados, com no mínimo 5 respondentes por grupo.</li></ul>",

        "<h2>Referências</h2>",
        "<p>Alves MGM, Chor D, Faerstein E, Lopes CS, Werneck GL. Versão resumida da “job stress scale”: adaptação "
        "para o português. Rev Saúde Pública. 2004;38(2):164-171.</p>",
        "<p>Aguiar OB, Fonseca MJM, Valente JG. Confiabilidade (teste-reteste) da escala sueca do Questionário "
        "Demanda-Controle entre Trabalhadores de Restaurantes Industriais. Rev Bras Epidemiol. 2010;13(2):212-222.</p>",
    ]
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>Estresse no trabalho por setor (JSS)</title><style>{ESTILO}</style></head><body>"
            + "\n".join(partes) + "</body></html>\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--privado", action="store_true")
    args = parser.parse_args()
    pasta = (RAIZ / "data" / "privado" if args.privado else RAIZ) / "resultados"
    (pasta / "relatorio.html").write_text(montar(pasta, sintetico=not args.privado), encoding="utf-8", newline="\n")
    print("gravado:", (pasta / "relatorio.html").relative_to(RAIZ))
