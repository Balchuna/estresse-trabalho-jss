# Método de pontuação

## O instrumento

Versão resumida da Job Stress Scale (também chamada de escala sueca de demanda-controle-apoio social), criada por Töres Theorell em 1988 a partir do questionário de Karasek e adaptada para o português por Alves e colaboradores. São 17 perguntas em três dimensões.

O texto das perguntas não é reproduzido aqui (ver `docs/DECISOES.md`). A tabela abaixo usa os códigos do projeto e a letra de cada item na Tabela 3 do artigo.

| Dimensão | Itens no projeto | Itens no artigo | Faixa do escore |
|---|---|---|---|
| Demanda | `q01` a `q05` | a, b, c, d, e | 5 a 20 |
| Controle | `q06` a `q11` | f, g, h, i, j, k | 6 a 24 |
| Apoio social | `q12` a `q17` | l, m, n, o, p, q | 6 a 24 |

O controle tem duas subdimensões: discernimento intelectual (uso de habilidades, `q06` a `q09`) e autoridade sobre decisões (`q10` e `q11`).

## Pontos de cada resposta

| Perguntas | Resposta | Pontos |
|---|---|---|
| `q01` a `q11` | Frequentemente / Às vezes / Raramente / Nunca ou quase nunca | 4 / 3 / 2 / 1 |
| `q12` a `q17` | Concordo totalmente / Concordo mais que discordo / Discordo mais que concordo / Discordo | 4 / 3 / 2 / 1 |

## Itens invertidos

Dois itens apontam na direção contrária da sua dimensão e têm os pontos invertidos (1 / 2 / 3 / 4, ou seja, `5 - pontos`):

- `q04` (item d, ter tempo suficiente para as tarefas): quanto mais frequente, **menor** a demanda;
- `q09` (item i, repetir muitas vezes as mesmas tarefas): quanto mais frequente, **menor** o controle.

Nenhum item de apoio social é invertido.

## Escore

O escore de cada dimensão é a **soma** dos pontos dos seus itens. Mais pontos significam mais demanda, mais controle ou mais apoio.

Quem deixou em branco algum item de uma dimensão fica sem escore naquela dimensão. Nada é preenchido por estimativa.

## De onde vem cada regra

| Regra | Fonte | Onde |
|---|---|---|
| 17 itens: 5 de demanda, 6 de controle, 6 de apoio | Alves et al. (2004) | Introdução e Tabela 3 |
| Ordem dos itens e opções de resposta | Alves et al. (2004) | Tabela 3 |
| Subdimensões do controle (4 + 2 itens) | Alves et al. (2004) | Introdução e Tabela 2 |
| Escala de 1 a 4 | Alves et al. (2004) | Introdução: "escala tipo Likert (1-4)" |
| Pontos 4/3/2/1 de cada opção | Aguiar et al. (2010) | Métodos |
| Itens invertidos (tempo suficiente; repetir tarefas) | Aguiar et al. (2010) | Métodos |
| Escore por soma e faixas 5 a 20 e 6 a 24 | Aguiar et al. (2010) | Métodos |

**Atenção:** o artigo de Alves et al. (2004) descreve a adaptação, mas **não** diz quais itens são invertidos nem como somar. Essas regras foram confirmadas em Aguiar et al. (2010), que aplica a mesma versão brasileira e cita Alves et al.

Referências:

- Alves MGM, Chor D, Faerstein E, Lopes CS, Werneck GL. Versão resumida da "job stress scale": adaptação para o português. Rev Saúde Pública. 2004;38(2):164-171. https://doi.org/10.1590/S0034-89102004000200003
- Aguiar OB, Fonseca MJM, Valente JG. Confiabilidade (teste-reteste) da escala sueca do Questionário Demanda-Controle entre Trabalhadores de Restaurantes Industriais. Rev Bras Epidemiol. 2010;13(2):212-222. https://doi.org/10.1590/S1415-790X2010000200004

## Diferença entre o formulário e o artigo

No artigo, a quarta opção de apoio social é "Discordo totalmente". O formulário de origem usa só "Discordo". O projeto aceita o rótulo do formulário e dá a ele 1 ponto. É uma diferença de redação, registrada aqui como limitação.

## Quadrantes e apoio (critério do projeto)

Os dois artigos acima não definem ponto de corte. O projeto usa o critério mais comum na literatura do modelo demanda-controle: a **mediana da própria amostra** (todos os respondentes juntos).

- Demanda alta: escore **acima** da mediana de demanda. Igual à mediana conta como baixa.
- Controle alto: escore **acima** da mediana de controle.
- Apoio alto: escore **acima** da mediana de apoio.

| | Controle baixo | Controle alto |
|---|---|---|
| **Demanda alta** | Alta exigência | Trabalho ativo |
| **Demanda baixa** | Trabalho passivo | Baixa exigência |

Consequências desse critério:

- "alto" e "baixo" são relativos a este grupo de respondentes, não a uma norma externa;
- como os escores são números inteiros, muita gente empata na mediana, e os grupos não ficam metade a metade.

## Outras medidas

- **Alfa de Cronbach** por dimensão, calculado só com quem respondeu todos os itens da dimensão: `alfa = k/(k-1) × (1 − soma das variâncias dos itens ÷ variância da soma)`. Para comparação, Alves et al. (2004) relatam 0,79 (demanda), 0,67 (controle) e 0,85 (apoio).
- **Comparação entre unidades:** teste de Mann-Whitney (não paramétrico, bilateral), porque os escores são ordinais e a amostra é pequena. Tamanho de efeito: correlação bisserial por postos, `r = 2·U₁/(n₁·n₂) − 1`, de −1 a 1; positivo quer dizer escores maiores na Unidade 1.

## Onde está no código

- `src/jss/pontuacao.py`: pontos, inversão e soma.
- `src/jss/analise.py`: cortes, quadrantes, alfa, descritivos e comparação.
- `tests/test_pontuacao.py`: cada opção de resposta, os dois itens invertidos, os extremos de cada faixa e um caso calculado à mão.
