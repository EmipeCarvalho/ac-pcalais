# Relatório de qualidade — protocolo e estado atual

## Objetivo

Extrair cardápios de imagens da Web, validar a qualidade e persistir os dados com orquestração Prefect. A POC implementa a abordagem multimodal proposta na atividade.

## Estado atual

O software possui testes locais de validação, armazenamento e fluxo Prefect. A chamada multimodal é simulada nesses testes. Não foi executada a avaliação real de 50 cardápios, porque não foi fornecida chave Gemini nem um conjunto de 50 imagens. Assim, este documento descreve o protocolo, não resultados de um experimento concluído.

## Amostragem e reprodutibilidade

Coletar pelo menos 50 imagens distintas com URLs, hash, data de coleta e características de layout. Registrar autorização/licença da fonte. Incluir diferentes restaurantes e qualidade de imagem. Uma opção pública para pesquisa é o dataset https://huggingface.co/datasets/shivank21/mmconflict-restaurant-menus-500. Inspecionar as condições e as imagens antes de usar. Não reutilizar suas anotações como se fossem saídas do pipeline.

Fixar modelo, data do experimento, parâmetros, teto por moeda, tarifas e versões de dependências. Usar banco exclusivo. Deduplicar por hash. Não substituir imagens difíceis apenas porque produzem erros.

## Execução

```bash
python -m menu_atlas.collect data/manifest.csv
python -m menu_atlas.batch data/manifest.csv --db data/evaluation.sqlite
```

Anexar o manifesto, banco povoado e arquivos gerados em reports/. O relatório automático consolida os resultados reais. Não interpretar uma falha como cardápio com zero missing.

## Resultados obrigatórios

| Indicador | Estado |
|---|---|
| Cardápios distintos processados | Aguardando execução real |
| Missing data | Aguardando execução real |
| Preços razoáveis | Aguardando execução real |
| Latência média | Aguardando execução real |
| Custo médio e tokens | Aguardando execução real |

## Discussão após o experimento

Para cada classe de problema, selecionar exemplos reais e comparar foto e JSON: colunas misturadas, descrições atribuídas ao item errado, preço de variante, reflexo, baixa resolução e moeda ausente. Quantificar falhas por categoria de layout. Registrar percentual de chamadas que falharam.

Conferir manualmente uma amostra estratificada e medir nomes/preços corretos em relação à imagem. As quatro métricas de plausibilidade exigidas não medem sozinhas a acurácia da transcrição. Em especial, itens omitidos por completo não entram no denominador de missing de campos e precisam ser avaliados pela comparação visual.
