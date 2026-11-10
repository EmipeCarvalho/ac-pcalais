# Dicionário de dados

## runs

Uma linha por tentativa. `id` é a chave primária.

| Campo | Tipo | Significado |
|---|---|---|
| id | TEXT | UUID da execução |
| created_at | TEXT | Data/hora UTC do SQLite |
| source | TEXT | URL de origem ou nome do upload |
| image_sha256 | TEXT | Hash dos bytes originais |
| restaurant | TEXT, nulo | Nome transcrito |
| model | TEXT | Identificador do modelo, unknown se falha anterior |
| status | TEXT | valid, review ou failed |
| elapsed_seconds | REAL | Tempo até commit de dados |
| input_tokens | INTEGER, nulo | Tokens de entrada reportados pelo provedor |
| output_tokens | INTEGER, nulo | Tokens da resposta |
| thinking_tokens | INTEGER, nulo | Tokens de pensamento reportados |
| estimated_cost_usd | REAL, nulo | Estimativa conforme tarifas configuradas |
| item_count | INTEGER | Quantidade extraída antes de filtrar |
| missing_cells | INTEGER | Células obrigatórias nulas |
| required_cells | INTEGER | Quatro vezes o número de itens |
| reasonable_prices | INTEGER | Preços que passam pelo intervalo |
| raw_json | TEXT | JSON transcrito preservado |
| validation_json | TEXT | Auditoria de regras e itens |
| error | TEXT, nulo | Mensagem sanitizada da falha |

## items

Uma linha por produto/variante. `run_id` referencia `runs.id`.

| Campo | Tipo | Significado |
|---|---|---|
| id | INTEGER | Chave autoincrementada |
| run_id | TEXT | UUID da execução |
| category | TEXT, nulo | Categoria explícita |
| name | TEXT, nulo | Nome e variante |
| description | TEXT, nulo | Descrição transcrita |
| price | REAL, nulo | Valor na unidade monetária original |
| currency | TEXT, nulo | Código de três letras, ex. BRL |
| attributes | TEXT | Lista JSON de atributos explícitos |
| status | TEXT | valid ou review |
| issues | TEXT | Lista JSON dos motivos de revisão |

SQLite REAL usa ponto flutuante, suficiente para esta POC. Para faturamento financeiro, migrar preços para unidades inteiras ou DECIMAL. Não consolidar moedas distintas em somas de valores.
