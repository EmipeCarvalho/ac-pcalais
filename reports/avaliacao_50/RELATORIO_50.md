# Avaliação real de 50 cardápios

Execução em 10/11/2026. Modelo: `gpt-5-mini-2025-08-07`, reasoning `low`, limite de saída 32.000 tokens. As 50 imagens têm URLs e SHA-256 no manifesto. Quatro flows Prefect processaram imagens concorrentemente. Nenhuma resposta da IA foi simulada nesta avaliação.

| Indicador | Resultado |
|---|---|
| Imagens distintas processadas | 50 |
| Falhas de API/pipeline | 0 |
| Aprovados pelos guardrails | 37 |
| Para revisão humana | 13 |
| Imagens sem itens | 1 |
| Itens/variantes extraídos | 1289 |
| Missing de campos obrigatórios | 0.36% |
| Itens com preço razoável | 98.84% |
| Preços ausentes | 14 |
| Preços fora da faixa | 1 |
| Latência média por imagem (s) | 18.814 |
| Latência média original antes da revalidação (s) | 18.694 |
| Tempo total do lote concorrente (s) | 272.8 |
| Custo total estimado (USD) | 0.173299 |
| Custo médio estimado por imagem (USD) | 0.003466 |

## Metodologia e correção identificada no lote

A primeira validação marcou 42 imagens para revisão. Ela continha uma lista limitada de moedas que rejeitava INR e outros códigos válidos. A regra foi corrigida para consultar ISO 4217 por pycountry, e todas as 50 extrações salvas foram revalidadas localmente, sem repetir chamadas à API. Os resultados acima usam a regra corrigida. As verificações originais permanecem em `initial_validation` e `initial_run` em cada JSON de auditoria.

A latência final por imagem é a latência original do flow mais o tempo medido da revalidação offline. O CSV também conserva as duas durações separadas. O tempo de parede do lote mede as chamadas concorrentes originais e não inclui a revalidação posterior. A atualização da própria medição não entra na latência.

Missing usa categoria, nome e preço. Preços razoáveis incluem todos os itens no denominador, incluindo os sem preço. Faixa configurada: 1 a 1.500 na moeda original. Os valores monetários não foram convertidos. Essa faixa única é uma limitação em uma amostra com várias moedas.

Custo calculado com as tarifas informadas: USD 0,25 por milhão de tokens de entrada e USD 2,00 por milhão de tokens de saída. É uma estimativa baseada no uso retornado; conferir faturamento no provedor.

## Verificações que exigiram revisão

| Regra | Imagens que falharam |
|---|---|
| Preço preenchido em todos os itens | 7 |
| Nenhum item com o mesmo nome da categoria (cabeçalho lido como item) | 5 |
| Moeda em código ISO (BRL, USD…) | 3 |
| Preço razoável (1 a 1500) | 1 |
| Preços das variações seguem a ordem dos tamanhos (P < M < G) | 1 |
| Cardápio tem ao menos 1 item | 1 |
| Nenhum item repetido na mesma categoria | 1 |

## Moedas identificadas pelo modelo

| Código | Imagens |
|---|---|
| INR | 39 |
|  | 4 |
| USD | 1 |
| BRL | 3 |
| null | 3 |

## Conferência visual e limitações

Uma conferência pontual da imagem `web_restaurant_menu_0000.jpg` confirmou os preços 15/20, 30/35 e 50/55 nas três primeiras opções de pães. A extração preservou esses seis valores em linhas de variantes. Isso é uma amostra pontual, não uma medição de acurácia do conjunto inteiro. A moeda INR nessa imagem não está explicitamente visível, portanto sua atribuição é uma inferência do modelo.

A imagem `web_restaurant_menu_0035.jpg` contém um cardápio em devanágari, com texto pequeno e várias fotos. O modelo reconheceu o cardápio, mas retornou zero itens e relatou legibilidade insuficiente. O pipeline direcionou esse resultado à revisão. Esse caso demonstra uma falha de cobertura: a taxa de missing por campo não mede itens completamente omitidos.

Aprovação dos guardrails indica plausibilidade e consistência, não fidelidade garantida à imagem. Não existe ground truth completo anotado pela dupla para afirmar acurácia de transcrição. Os 50 arquivos representam um conjunto de conveniência multilíngue, não uma amostra representativa de restaurantes brasileiros.

## Resultado por imagem

| Arquivo | Status | Itens | Validações | Tempo (s) | Custo USD |
|---|---|---|---|---|---|
| web_restaurant_menu_0000.jpg | aprovado | 44 | 15/15 | 36.62 | 0.005509 |
| web_restaurant_menu_0001.jpg | revisao_humana | 15 | 14/15 | 19.04 | 0.002428 |
| web_restaurant_menu_0002.jpg | aprovado | 15 | 15/15 | 18.72 | 0.002341 |
| web_restaurant_menu_0003.jpg | revisao_humana | 36 | 13/15 | 35.11 | 0.004898 |
| web_restaurant_menu_0004.jpg | aprovado | 12 | 15/15 | 10.86 | 0.001885 |
| web_restaurant_menu_0005.jpg | aprovado | 10 | 15/15 | 15.84 | 0.002709 |
| web_restaurant_menu_0006.jpg | aprovado | 11 | 15/15 | 12.06 | 0.002303 |
| web_restaurant_menu_0007.jpg | revisao_humana | 43 | 14/15 | 28.63 | 0.005955 |
| web_restaurant_menu_0008.jpg | aprovado | 7 | 14/15 | 10.14 | 0.001974 |
| web_restaurant_menu_0009.jpg | aprovado | 18 | 15/15 | 11.47 | 0.002392 |
| web_restaurant_menu_0010.jpg | revisao_humana | 61 | 14/15 | 37.50 | 0.007723 |
| web_restaurant_menu_0011.jpg | aprovado | 16 | 15/15 | 11.89 | 0.002587 |
| web_restaurant_menu_0012.jpg | aprovado | 4 | 15/15 | 5.80 | 0.001966 |
| web_restaurant_menu_0013.jpg | aprovado | 16 | 15/15 | 10.31 | 0.002422 |
| web_restaurant_menu_0014.jpg | aprovado | 13 | 15/15 | 10.44 | 0.002229 |
| web_restaurant_menu_0015.jpg | aprovado | 4 | 15/15 | 6.80 | 0.001486 |
| web_restaurant_menu_0016.jpg | aprovado | 24 | 15/15 | 14.50 | 0.002877 |
| web_restaurant_menu_0017.jpg | aprovado | 22 | 15/15 | 16.74 | 0.003280 |
| web_restaurant_menu_0018.jpg | aprovado | 33 | 15/15 | 25.43 | 0.004844 |
| web_restaurant_menu_0019.jpg | aprovado | 34 | 15/15 | 18.43 | 0.003527 |
| web_restaurant_menu_0020.jpg | aprovado | 5 | 15/15 | 7.84 | 0.001328 |
| web_restaurant_menu_0021.jpg | aprovado | 11 | 15/15 | 9.23 | 0.001798 |
| web_restaurant_menu_0022.jpg | aprovado | 18 | 14/15 | 16.49 | 0.003388 |
| web_restaurant_menu_0023.jpg | revisao_humana | 23 | 14/15 | 16.71 | 0.003456 |
| web_restaurant_menu_0024.jpg | revisao_humana | 7 | 14/15 | 6.25 | 0.001331 |
| web_restaurant_menu_0025.jpg | aprovado | 32 | 15/15 | 18.17 | 0.003804 |
| web_restaurant_menu_0026.jpg | aprovado | 18 | 15/15 | 10.85 | 0.002310 |
| web_restaurant_menu_0027.jpg | revisao_humana | 4 | 14/15 | 7.87 | 0.001616 |
| web_restaurant_menu_0028.jpg | aprovado | 23 | 15/15 | 12.94 | 0.002780 |
| web_restaurant_menu_0029.jpg | aprovado | 14 | 15/15 | 8.65 | 0.001860 |
| web_restaurant_menu_0030.jpg | aprovado | 16 | 15/15 | 11.99 | 0.002504 |
| web_restaurant_menu_0031.jpg | aprovado | 24 | 14/15 | 23.76 | 0.004382 |
| web_restaurant_menu_0032.jpg | revisao_humana | 44 | 14/15 | 31.59 | 0.005162 |
| web_restaurant_menu_0033.jpg | revisao_humana | 174 | 14/15 | 79.98 | 0.013572 |
| web_restaurant_menu_0034.jpg | aprovado | 19 | 15/15 | 15.20 | 0.002641 |
| web_restaurant_menu_0035.jpg | revisao_humana | 0 | 14/15 | 7.11 | 0.001107 |
| web_restaurant_menu_0036.jpg | revisao_humana | 65 | 13/15 | 42.65 | 0.007433 |
| web_restaurant_menu_0037.jpg | aprovado | 10 | 15/15 | 12.13 | 0.002104 |
| web_restaurant_menu_0038.jpg | aprovado | 5 | 15/15 | 7.40 | 0.001391 |
| web_restaurant_menu_0039.jpg | aprovado | 7 | 15/15 | 12.73 | 0.002551 |
| web_restaurant_menu_0040.jpg | aprovado | 29 | 15/15 | 18.41 | 0.003620 |
| web_restaurant_menu_0041.jpg | revisao_humana | 41 | 14/15 | 27.51 | 0.005637 |
| web_restaurant_menu_0042.jpg | aprovado | 9 | 15/15 | 8.72 | 0.001767 |
| web_restaurant_menu_0043.jpg | aprovado | 30 | 14/15 | 22.09 | 0.003896 |
| web_restaurant_menu_0044.jpg | revisao_humana | 28 | 14/15 | 26.38 | 0.004266 |
| web_restaurant_menu_0045.jpg | aprovado | 16 | 15/15 | 17.08 | 0.002768 |
| web_restaurant_menu_0046.jpg | aprovado | 12 | 15/15 | 11.66 | 0.001823 |
| web_restaurant_menu_0047.jpg | aprovado | 118 | 15/15 | 59.09 | 0.011119 |
| web_restaurant_menu_0048.jpg | aprovado | 46 | 15/15 | 28.55 | 0.005408 |
| web_restaurant_menu_0049.jpg | aprovado | 3 | 15/15 | 5.36 | 0.001142 |

## Arquivos e reprodução

- `menu_items.csv`: catálogo consolidado com todos os itens e flags.
- `pipeline_runs.csv`: execuções, hashes, uso de tokens, custos e durações.
- `resultados_por_cardapio.csv`: resultados vinculados às URLs de origem.
- `metrics.json`: indicadores consolidados.
- `extracoes/`: JSONs completos, com auditoria original e revalidação.

O arquivo `resultados_completos.zip` reúne esses dados e o manifesto. A chave API não faz parte dos resultados. Os CSVs históricos do projeto foram preservados e não participam das métricas deste lote.