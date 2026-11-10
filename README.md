# Cardápios ETL — POC inspirada no pipeline da DoorDash

Este projeto extrai dados estruturados de fotos de cardápios usando um **modelo multimodal** (OpenAI GPT, Abordagem 2), aplica **guardrails com Great Expectations** e persiste o resultado em um **CSV consolidado**. Todo o fluxo é orquestrado com **Prefect**. A interface gráfica é em **Streamlit**.

```
foto ──► [pre-processar-imagem] ──► [extrair-com-modelo-multimodal] ──► [estruturar-e-normalizar]
                                                                              │
         output/menu_items.csv ◄── [persistir-csv] ◄── [validar-com-great-expectations]
         output/pipeline_runs.csv
```

| Task do Prefect | O que faz |
|---|---|
| `pre-processar-imagem` | Corrige a rotação EXIF de fotos de celular, converte para RGB e limita o tamanho a 2000 px |
| `extrair-com-modelo-multimodal` | Envia imagem + prompt ao GPT (Responses API, Structured Outputs), com saída validada por um schema Pydantic (`pipeline/schemas.py`). Sem retries automáticos para evitar duplicação de chamadas pagas |
| `estruturar-e-normalizar` | Achata a hierarquia categoria → item → variação em linhas e limpa os textos |
| `validar-com-great-expectations` | Roda 15 expectativas (preços, nulos, consistência, formato, duplicidade) e decide entre aprovado e revisão humana |
| `persistir-csv` | Faz append em `menu_items.csv` e `pipeline_runs.csv` |

## Estrutura

```
backend/
  pipeline/config.py        configurações (.env)
  pipeline/schemas.py       schema de saída do modelo
  pipeline/extractor.py     chamada ao modelo multimodal + custo
  pipeline/validation.py    suíte do Great Expectations (guardrails)
  pipeline/flow.py          @tasks e @flow do Prefect
  pipeline/storage.py       append nos CSVs
  pipeline/metrics.py       métricas do relatório
  app.py     interface gráfica
  scripts/run_batch.py avaliação em larga escala + relatório
data/                  imagens dos cardápios (entrada do lote)
output/                CSVs gerados
reports/               quality_report.md + metrics.json
docs/DICIONARIO_DE_DADOS.md
```

## Como rodar

Os comandos abaixo são para o terminal do Windows (PowerShell ou o terminal do VS Code) e partem da raiz do projeto. Eles chamam o Python do ambiente virtual direto (`.venv\Scripts\python`), então não é preciso ativar o ambiente.

### Primeira instalação (só uma vez)
```powershell
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
```
Depois, abra `backend/.env` e preencha:
- `OPENAI_API_KEY`: a sua chave da OpenAI;
- `PRICE_INPUT_PER_1M` e `PRICE_OUTPUT_PER_1M`: os preços do modelo, usados no cálculo de custo.

### Iniciar a aplicação
```powershell
cd backend
.venv\Scripts\python -m streamlit run app.py
```
A interface abre em http://localhost:8501. Com uma foto, você acompanha cada etapa do pipeline. Com várias, elas são processadas em lote, com barra de progresso e uma tabela de resultados.

### Processar o lote de cardápios (relatório de qualidade)
Coloque as imagens em `data/` e rode:
```powershell
cd backend
.venv\Scripts\python -m scripts.run_batch                # processa os que ainda não foram processados
.venv\Scripts\python -m scripts.run_batch --force        # reprocessa todos
.venv\Scripts\python -m scripts.run_batch --report-only  # só regenera o relatório a partir dos CSVs
```
O comando gera `reports/quality_report.md` e `reports/metrics.json` com:
- % de missing data;
- % de preços razoáveis;
- latência média;
- custo médio por cardápio.

### (Opcional) Acompanhar os flows na interface do Prefect
Sem servidor configurado, o Prefect sobe um servidor temporário a cada execução. Para ver o histórico dos flows na interface web:
```powershell
# terminal 1
cd backend
.venv\Scripts\prefect server start                                    # http://127.0.0.1:4200

# terminal 2 (uma vez), depois inicie a aplicação normalmente
cd backend
.venv\Scripts\prefect config set PREFECT_API_URL=http://127.0.0.1:4200/api
```

## Configuração (`backend/.env`)
| Variável | Padrão | Descrição |
|---|---|---|
| `OPENAI_API_KEY` | — | Chave da API da OpenAI |
| `OPENAI_MODEL` | `gpt-5-mini` | Modelo multimodal. `gpt-5-mini` foi o mais barato que extraiu os cardápios completos nos testes; o `gpt-5-nano` é ~5x mais barato, mas pulou itens |
| `OPENAI_REASONING_EFFORT` | `low` | `low`/`medium`/`high`. Deixe vazio para modelos sem raciocínio (ex.: `gpt-4.1`) |
| `PRICE_INPUT_PER_1M` / `PRICE_OUTPUT_PER_1M` | `0.25` / `2.00` | Preço do modelo em US$ por 1M de tokens, usado no cálculo de custo |
| `PRICE_MIN` / `PRICE_MAX` | `1` / `1500` | Faixa de preço considerada razoável |
| `REVIEW_THRESHOLD` | `0.85` | Fração mínima de expectativas aprovadas, além da aprovação de todas as regras essenciais |


## Correções e avaliação reproduzível

Esta versão exige aprovação de todas as regras essenciais de preço, campos obrigatórios, texto e duplicidade. O limiar de 85% não pode compensar uma falha essencial. Preços ausentes entram no denominador de preços razoáveis. A interface trata resultados vazios, custos desconhecidos e histórico apenas com falhas.

A latência das novas execuções é medida após o append dos dois CSVs. Os dois níveis de retries automáticos foram desativados. Uma falha sem uso reportado recebe custo desconhecido, nunca zero. O relatório separa subtotal conhecido e total incompleto. Tarifas ausentes geram custo desconhecido; preencha as tarifas vigentes do modelo efetivamente usado.

### Coleta dos 50 cardápios com fontes

A partir de backend/:

```powershell
.venv\Scripts\python -m scripts.collect_menus
.venv\Scripts\python -m scripts.run_batch --manifest ../data/manifest.csv
```

O manifesto inclui 50 imagens públicas distintas com URLs e SHA-256, verificadas durante o desenvolvimento. O coletor baixa os arquivos no computador da dupla. A execução real precisa da chave OpenAI local. Use `--delay 5` se quiser espaçar chamadas e `--force` somente quando desejar pagar por um novo processamento.

A retomada usa hashes, não nomes de arquivo. Somente execuções novas com hashes comprovam imagens distintas. Rodar a mesma imagem 50 vezes não atende à meta. O relatório indica explicitamente se existem pelo menos 50 imagens distintas processadas sem erro.

Os dez exemplos e CSVs originais foram preservados como evidência histórica. Seus status e tempos refletem a implementação anterior e não foram reescritos como se tivessem sido medidos pela nova versão. Para o experimento final, arquive os CSVs históricos antes de iniciar o lote, evitando misturar versões. Consulte [a análise e as pendências](docs/AVALIACAO.md) e [as fontes](data/FONTES.md).

### Testes sem consumir créditos

Na raiz do repositório, com o ambiente virtual instalado:

```powershell
backend\.venv\Scripts\python -m pip install pytest
backend\.venv\Scripts\python -m pytest -q
```

Os testes exercitam Great Expectations, Streamlit, CSV e um flow Prefect real. Somente a chamada à API é simulada. Não confundir esses testes com a avaliação real dos 50 cardápios.
