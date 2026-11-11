# Decisões

## Fase 1 (11/11/2026)

1. **Repositório com dados sintéticos.** Não há autorização da empresa para usar as respostas reais em portfólio. A análise real, se for feita, fica só no computador, em pastas ignoradas pelo git.

2. **O texto das perguntas não entra no repositório.** O artigo da adaptação brasileira (Alves et al., 2004) é distribuído sob CC BY-NC 4.0 (uso não comercial), e uma nota do artigo diz que os direitos da adaptação foram cedidos aos autores por Töres Theorell. Não há autorização geral para reproduzir os itens. Por isso as colunas são `q01` a `q17` e o artigo é citado. Os nomes das opções de resposta ("Frequentemente", "Concordo totalmente" etc.) são rótulos genéricos de escala e foram mantidos.

3. **Perguntas identificadas pela posição.** Como o texto não fica guardado, a limpeza confia na ordem das colunas. Para isso ser seguro, ela exige exatamente 17 perguntas e compara o texto das duas unidades em memória; a mensagem de erro cita só a posição.

4. **Distribuições inventadas, não copiadas.** O gerador usa setores, tamanhos (80 e 50) e tendências inventados. Calibrar o gerador pelas distribuições reais por setor publicaria, na prática, um retrato agregado de dados sem autorização. *Pendente de confirmação.*

5. **Colunas pessoais descartadas na leitura.** Usar `usecols` é mais seguro do que carregar tudo e apagar depois: não existe um momento em que a tabela tenha e-mail ou horário.

6. **Mínimo de 5 por setor, contado dentro de cada unidade.** A análise será por setor e unidade, então é nesse cruzamento que o grupo pequeno aparece. Se o próprio "Outros" ficar abaixo de 5, o resumo de qualidade avisa (`unidades_com_outros_abaixo_do_minimo`) e a análise não poderá mostrá-lo separado.

7. **Resposta vazia ou fora da escala vira ausente.** Nada é corrigido nem adivinhado; só é contado. Como tratar ausentes na pontuação é decisão da fase 2.

8. **Linhas embaralhadas com semente fixa.** Apaga a ordem de chegada das respostas sem perder a reprodutibilidade.

9. **Rótulos em texto, sem números ainda.** A conversão das respostas em pontos (e os itens invertidos) depende de confirmar o método no artigo original. Fica para a fase 2.
