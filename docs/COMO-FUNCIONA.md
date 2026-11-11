# Como funciona (fase 1)

## O ponto de partida

Um formulário online exporta um CSV por unidade. Cada linha é uma pessoa. As colunas são: um ID, a hora de início e de conclusão, às vezes um e-mail, o setor e 17 perguntas.

Esse arquivo tem dois problemas:

- **Tem dado pessoal.** ID, horários e e-mail ajudam a descobrir quem respondeu.
- **É bagunçado.** A mesma resposta aparece como `Às vezes`, `Às vezes ` (com espaço) e `Às vezes` seguido de um espaço não separável, um caractere invisível que o formulário deixa. Para o computador, são três respostas diferentes.

## O que a limpeza faz, em ordem

1. **Descobre a codificação.** Tenta ler como UTF-8. Se der erro, lê como cp1252 (o padrão antigo do Windows). Ler com a codificação errada é o que faz `Produção` virar `ProduÃ§Ã£o`.
2. **Joga fora as colunas pessoais já na leitura.** O programa diz ao pandas quais colunas carregar (`usecols`). ID, horários, e-mail e nome nunca entram na tabela, então não há como vazarem depois.
3. **Padroniza os textos.** Troca o espaço não separável por espaço comum e corta espaços sobrando, em cabeçalhos, setores e respostas.
4. **Confere a estrutura.** Tem de haver 1 coluna de setor e 17 perguntas. As duas unidades têm de ter as mesmas perguntas, na mesma ordem. Se não, o programa para com erro.
5. **Troca o texto das perguntas por códigos.** As colunas viram `q01` a `q17`, pela posição.
6. **Confere as respostas.** As perguntas 1 a 11 aceitam `Frequentemente`, `Às vezes`, `Raramente` e `Nunca ou quase nunca`. As perguntas 12 a 17 aceitam `Concordo totalmente`, `Concordo mais que discordo`, `Discordo mais que concordo` e `Discordo`. Resposta vazia ou diferente disso vira "ausente" e entra na contagem de qualidade.
7. **Protege grupos pequenos.** Em cada unidade, setor com menos de 5 pessoas vira "Outros". Num grupo de 2 pessoas, a média quase revela a resposta de cada uma.
8. **Embaralha as linhas.** A ordem original segue o horário da resposta. Embaralhar apaga essa pista.

## O que sai

- `respostas_limpas.csv`: colunas `unidade`, `setor`, `q01` a `q17`.
- `qualidade.json`: quantas pessoas, qual codificação, quantas colunas pessoais saíram, quantas respostas vazias ou fora da escala, quantos setores foram para "Outros".

## Dados fictícios e dados reais

O repositório só tem dados fictícios (`data/sintetico/`), criados por `scripts/gerar_dados.py` com os mesmos tipos de defeito de uma exportação real.

O mesmo programa limpa dados reais no computador de quem tem o direito de usá-los: `python scripts/limpar.py --entrada data/raw`. As pastas `data/raw/` e `data/privado/` estão no `.gitignore` e nunca são publicadas.

## Como os testes provam isso

- Arquivos pequenos, montados dentro do teste, com cada defeito: codificação cp1252, ponto e vírgula, espaços, resposta fora da escala, pergunta faltando, perguntas diferentes entre unidades, setor pequeno.
- O gerador é conferido byte a byte: a mesma semente dá sempre os mesmos arquivos, iguais aos do repositório.
- A saída da limpeza é varrida atrás de horário, e-mail e espaço não separável.

# Como funciona (fases 2 a 4)

## Da resposta ao escore

Cada resposta vira um número de 1 a 4. "Frequentemente" e "Concordo totalmente" valem 4; "Nunca ou quase nunca" e "Discordo" valem 1.

Dois itens são **invertidos**. Exemplo: responder "Frequentemente" a "tenho tempo suficiente" indica **pouca** demanda, então vale 1 em vez de 4. A conta é `5 − pontos`.

Depois é só somar: demanda (5 itens, de 5 a 20), controle (6 itens, de 6 a 24) e apoio social (6 itens, de 6 a 24).

## Do escore ao quadrante

Calculo a mediana de demanda e a de controle entre todos os respondentes. Quem está acima da mediana é "alto".

- demanda alta + controle baixo = **alta exigência** (o grupo que mais preocupa);
- demanda alta + controle alto = trabalho ativo;
- demanda baixa + controle baixo = trabalho passivo;
- demanda baixa + controle alto = baixa exigência.

O apoio social entra à parte: alto ou baixo, também pela mediana.

## As três conferências

- **Alfa de Cronbach:** os itens de uma dimensão andam juntos? Se sim, o alfa fica perto de 1.
- **Descritivo:** média, desvio-padrão e mediana por unidade e por setor, mais o percentual em alta exigência.
- **Mann-Whitney:** as duas unidades diferem? O teste compara a posição das pessoas numa fila ordenada pelo escore. O tamanho de efeito (de −1 a 1) diz se a diferença é grande.

## O relatório

`scripts/gerar_relatorio.py` lê as tabelas de `resultados/` e monta um HTML com resumo, método, resultados, limitações e uso no PGR. A seção "Interpretação" é lida de `docs/INTERPRETACAO.md`, que o autor escreve.
