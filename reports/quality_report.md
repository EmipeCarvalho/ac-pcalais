# Relatório de qualidade
Gerado em 2026-11-10T14:56:59.702415+00:00

Resultados reais dos CSVs atuais. A contagem de imagens distintas considera somente hashes registrados.
Execuções antigas sem hash não comprovam a meta de 50 imagens distintas.

| Indicador | Valor |
|---|---|
| menus_processados | 10 |
| menus_distintos_verificados | 0 |
| menus_distintos_sem_erro | 0 |
| meta_50_cardapios_atingida | False |
| menus_com_erro | 0 |
| menus_aprovados | 10 |
| menus_revisao_humana | 0 |
| itens_extraidos | 182 |
| pct_missing_data | 2.2 |
| pct_linhas_com_campo_faltante | 6.59 |
| pct_precos_razoaveis | 93.41 |
| precos_ausentes | 12 |
| precos_fora_da_faixa | 0 |
| faixa_preco_razoavel | [1.0, 1500.0] |
| latencia_media_s | 12.436 |
| latencia_p50_s | 12.195 |
| latencia_max_s | 21.81 |
| tokens_input_medio | 1367.4 |
| tokens_output_medio | 1406.7 |
| custo_medio_usd | 0.00255 |
| custo_total_usd | 0.025501 |
| custo_conhecido_usd | 0.025501 |
| execucoes_custo_desconhecido | 0 |
| score_gx_medio | 0.9933 |

## Configuração e interpretação
Modelos presentes nos registros: gpt-5-mini-2025-08-07, gpt-5.4-mini-2026-03-17.
Missing: categoria, nome e preço. Preços razoáveis: todos os itens no denominador, incluindo preços ausentes.
Custos desconhecidos não são zero. O custo conhecido é um subtotal, não o total faturado quando existem falhas sem uso reportado.
A latência das novas execuções inclui o append dos dois CSVs, sem a atualização posterior da própria medição.
Execuções antigas mantêm a latência e decisão de validação originais. Não reinterpretar esses registros como testes da versão corrigida.

## Evidências qualitativas
A análise está em docs/AVALIACAO.md. Para o lote final, registrar exemplos reais de layouts, ruído e erros de transcrição.