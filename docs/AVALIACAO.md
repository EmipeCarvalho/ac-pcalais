# Avaliação e estado da entrega

## Evidência histórica recebida

A versão original do repositório contém dez imagens, dez registros de execução, nove nomes de origem distintos e 182 linhas de itens. Doze preços estão ausentes. Todos os registros históricos dizem aprovado, decisão produzida pela regra anterior de pontuação. Não houve nova chamada paga nem reexecução desses cardápios nesta revisão.

Os CSVs incluem mais de um identificador de modelo da OpenAI. As tarifas precisam corresponder ao modelo de cada execução para conferir a estimativa histórica. Os registros sozinhos não permitem confirmar cada preço contra sua imagem nem atribuir fonte Web às imagens sem URL registrada.

## Falhas reproduzidas e corrigidas

- Cardápio com dois de três preços ausentes recebia aprovação. Agora exige revisão.
- Preço de 2.000 acima do teto de 1.500 recebia aprovação. Agora exige revisão.
- Resultado vazio causava KeyError na tabela da interface. Agora mostra mensagem sem tentar exportar colunas inexistentes.
- Histórico só com erros causava TypeError ao formatar métricas nulas. Agora exibe indicadores indisponíveis.
- A latência persistida era menor que a retornada ao usuário porque não incluía o armazenamento. Agora usa a medição após o append nos dois lugares.
- Retries no SDK e no Prefect podiam multiplicar chamadas. Agora uma execução corresponde a uma tentativa explícita, sem retry automático.
- Valores de custo desconhecidos podiam parecer gratuitos. Agora permanecem nulos e o relatório identifica custo incompleto.

Esses casos são testes controlados, com resposta de IA simulada. Não são resultados de 50 chamadas reais.

## Conjunto adicional

`data/manifest.csv` contém 50 imagens distintas com fonte pública e hash verificado. O conjunto é de conveniência e não representa estatisticamente restaurantes brasileiros. Há idiomas e moedas diferentes. A atribuição está em data/FONTES.md. As anotações do dataset não são utilizadas como saídas do pipeline.

## O que falta para concluir a atividade

1. Baixar as imagens pelo coletor e conferir layouts, legibilidade e moedas.
2. Configurar a chave OpenAI local e as tarifas correspondentes ao modelo. A chave não deve ser versionada.
3. Arquivar os CSVs históricos e executar o lote dos 50 cardápios.
4. Verificar no relatório pelo menos 50 hashes distintos processados sem erro.
5. Registrar missing, preços razoáveis, latência e custo reais. Falhas de API também entram na análise operacional.
6. Comparar visualmente saídas e imagens. Um preço plausível ainda pode estar errado e itens totalmente omitidos não aparecem na taxa de missing por campo.
7. Acrescentar exemplos reais e suas causas: múltiplas colunas, reflexo, texto pequeno, variantes e alucinação. Preparar a apresentação e testar uma foto inédita.

Não declaramos a avaliação concluída antes dessa execução. Os guardrails avaliam consistência e plausibilidade, não comprovam a acurácia da transcrição.


## Indicadores históricos recalculados

O relatório gerado sobre os CSVs recebidos contém 182 itens, 2,20% de células obrigatórias ausentes e 93,41% de itens com preço preenchido dentro da faixa. A ausência de preço afeta 6,59% das linhas. Esses números usam o denominador corrigido, mas não representam uma nova extração.

A latência média histórica registrada é 12,436 s e conserva a limitação da versão anterior (antes da persistência). O custo estimado histórico soma US$ 0,025501 conforme os valores existentes nos CSVs, sem validação independente do faturamento e das tarifas usadas. Os dez status históricos de aprovação foram preservados como evidência original, não como aprovação pelas regras corrigidas.
