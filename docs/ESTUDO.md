# Estudo: 10 perguntas prováveis de entrevista

Respostas curtas, baseadas no que este projeto realmente faz. Os números são dos dados fictícios (semente 20261111).

## 1. O que é o projeto, em uma frase?

Um pipeline em Python que pega as respostas de um questionário de estresse no trabalho (Job Stress Scale, 17 perguntas), limpa e anonimiza, calcula os escores de demanda, controle e apoio social e mostra em quais setores e unidades está a combinação de maior risco: demanda alta com controle baixo.

## 2. Por que os dados são sintéticos?

Porque as respostas reais são dados sensíveis de trabalhadores e não houve autorização da empresa para usá-las em portfólio. O repositório tem um gerador com semente fixa que cria 130 respondentes fictícios, com os mesmos defeitos de uma exportação real. O mesmo código roda em dados reais, numa pasta que o git ignora. Os setores e as tendências do gerador são inventados, não copiados dos dados reais.

## 3. Como você garantiu a anonimização?

Cinco cuidados: (1) ID, horários e e-mail são descartados na leitura, com `usecols`, então nunca existem na tabela; (2) empresa sem nome e unidades como "Unidade 1" e "Unidade 2"; (3) setor com menos de 5 pessoas vira "Outros", e a função de descritivo dá erro se aparecer grupo menor que 5; (4) as linhas são embaralhadas, porque a ordem original entrega o horário; (5) os testes varrem a saída atrás de horário, e-mail e espaço invisível.

## 4. Que problemas de qualidade você encontrou e como tratou?

Três: codificação (o programa tenta UTF-8 e, se falhar, usa cp1252); textos com espaço sobrando ou espaço não separável, que fazem a mesma resposta parecer três respostas diferentes; e resposta em branco. Padronizo os textos, confiro cada resposta contra a escala da pergunta e conto o que ficou vazio ou fora da escala num arquivo de qualidade. Não corrijo nem adivinho resposta.

## 5. Como funciona a pontuação? O que é um item invertido?

Cada resposta vale de 1 a 4 pontos e o escore da dimensão é a soma dos itens: demanda de 5 a 20, controle e apoio de 6 a 24. Dois itens apontam na direção contrária: "ter tempo suficiente" (mais tempo é menos demanda) e "repetir as mesmas tarefas" (mais repetição é menos controle). Neles a pontuação é `5 − pontos`. Se eu esquecesse de inverter, o erro apareceria no alfa de Cronbach, que despenca. Isso aconteceu de verdade durante o projeto: a primeira versão do gerador ignorava a inversão e o alfa da demanda saiu 0,32; corrigido, foi para 0,81.

## 6. De onde você tirou as regras? Como sabe que estão certas?

Os itens, as dimensões e as opções de resposta vêm de Alves et al. (2004), que adaptou a escala para o português. Esse artigo não diz quais itens são invertidos nem como somar; isso eu confirmei em Aguiar et al. (2010), que aplica a mesma versão. Está tudo em `docs/METODO.md`, com uma tabela "regra → fonte". Nos testes há um caso calculado à mão e os extremos de cada faixa.

## 7. O que são os quadrantes de Karasek e qual corte você usou?

O modelo cruza demanda e controle. Demanda alta com controle baixo é "alta exigência", o quadrante de maior risco; alta com alto é "trabalho ativo"; baixa com baixo é "trabalho passivo"; baixa com alto é "baixa exigência". O corte é a mediana de todos os respondentes; "alto" é estar acima dela. Limitação: o corte é relativo ao próprio grupo, e, como os escores são inteiros, há muitos empates. Nos dados fictícios, 34 de 129 pessoas (26%) ficaram em alta exigência.

## 8. O que é o alfa de Cronbach e o que você encontrou?

Mede se os itens de uma dimensão andam juntos, isto é, se parecem medir a mesma coisa. Vai até 1; acima de 0,70 costuma ser aceitável. Nos dados fictícios: 0,81 (demanda), 0,87 (controle) e 0,80 (apoio). São valores do gerador, então não dizem nada sobre a escala no mundo real; o artigo original relata 0,79, 0,67 e 0,85.

## 9. Por que Mann-Whitney e não teste t? O que é o tamanho de efeito?

Os escores são somas de respostas ordinais, com poucos valores possíveis e amostras pequenas, então preferi um teste que compara postos e não supõe distribuição normal. O valor de p diz se a diferença pode ser acaso; o tamanho de efeito diz se ela é grande. Usei a correlação bisserial por postos, de −1 a 1. Nos dados fictícios, o controle é menor na Unidade 2 (p = 0,0002; r = 0,39); em demanda e apoio não há diferença clara. Ressalvas: amostra pequena e três testes seguidos.

## 10. O que este resultado NÃO permite afirmar? E como seria usado numa empresa?

Não permite dizer que alguém está doente, nem que o setor causa adoecimento: é autorrelato, uma foto de um momento, e a escala é de rastreamento. Numa empresa, serviria como triagem dos fatores psicossociais no PGR: apontar setores para avaliação aprofundada (entrevistas, observação do trabalho) e servir de linha de base para medir de novo depois das mudanças. Sempre com resultados agregados e no mínimo 5 pessoas por grupo.
