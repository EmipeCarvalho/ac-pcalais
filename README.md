# Menu Atlas

Extração de cardápios com interface Streamlit, tipografia Inter, Gemini multimodal, Prefect 3, Great Expectations e SQLite.

## Começar

Requer Python 3.11 a 3.13. Recomendado: Python 3.12.

```bash
git clone https://github.com/EmipeCarvalho/ac-pcalais.git
cd ac-pcalais
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate
pip install -e ".[dev]"
```

Copie `.env.example` para `.env` e preencha `GEMINI_API_KEY`. Você também pode informar a chave somente na sessão pela interface. Obtenha a sua no Google AI Studio: https://aistudio.google.com/apikey. Nunca coloque chaves em commits.

```bash
streamlit run app.py
```

Abra http://localhost:8501. Envie uma foto, clique em **Extrair cardápios** e confira os itens, as validações e o JSON. O app suporta múltiplas imagens. Histórico e exportações ficam na Biblioteca.

Alternativa com Docker, após configurar `.env`:

```bash
docker compose up --build
```

## O que está implementado

- Preparação de imagens com orientação EXIF, limites de tamanho e normalização PNG.
- Saída JSON estruturada com Gemini e Pydantic, preservando campos desconhecidos como nulos.
- `@flow` do Prefect encadeando quatro tarefas: preparação, extração/estruturação, validação e armazenamento.
- Nove regras Great Expectations: quatro campos obrigatórios, preço positivo e dentro do limite, categoria consistente, duplicidade, comprimento do nome e formato da moeda.
- Quarentena lógica: cada item recebe `valid` ou `review`. As exportações aprovadas incluem somente itens válidos, enquanto o banco preserva toda a auditoria.
- Banco SQLite persistente e cumulativo, sem sobrescrever execuções anteriores.
- Lote por manifesto, deduplicação SHA-256 dentro do lote e relatório automático com as quatro métricas exigidas.
- Latência até o commit, tokens de entrada/saída/pensamento e custo quando tarifas foram configuradas.
- Testes automatizados e GitHub Actions.

## Prefect e observabilidade

Sem configuração, o Prefect abre um servidor temporário local para executar os flows. Para manter histórico de orquestração e visualizar tarefas:

```bash
prefect server start
# Em outro terminal, antes de iniciar o app:
prefect config set PREFECT_API_URL=http://127.0.0.1:4200/api
streamlit run app.py
```

Abra http://localhost:4200. As dependências entre tarefas são sequenciais e explícitas pelo retorno de cada etapa. Não há retry automático da API paga: evita reenvios e custos invisíveis. O usuário pode repetir uma tentativa com falha.

## Avaliação dos 50 cardápios

1. Colete pelo menos 50 imagens diferentes da Web. Inclua layouts de uma e várias colunas, fotos com ruído e idiomas/moedas identificáveis. Registre fonte e características no manifesto.
2. Use o modelo `data/manifest.example.csv` e crie `data/manifest.csv` com URLs reais e caminhos locais. O exemplo não é uma amostra real.
3. Se as imagens ainda não estiverem baixadas: `python -m menu_atlas.collect data/manifest.csv`.
4. Configure chave, modelo, tarifas e limite de preço adequado ao conjunto.
5. Execute o lote em um banco separado:

```bash
python -m menu_atlas.batch data/manifest.csv --db data/evaluation.sqlite
```

O comando gera `reports/metrics.json`, `reports/runs.csv`, `reports/report.md` e o SQLite povoado. Não preencha as métricas manualmente. Inspecione as falhas e complete a discussão qualitativa.

**Estado da entrega:** software implementado e testes locais aprovados. A extração real via Gemini e o lote de 50 imagens ainda dependem de uma chave de API e da coleta do conjunto. Não há alegação de 50 cardápios processados nem banco real povoado nesta versão. A apresentação e o relatório final precisam receber evidências dessa execução antes da entrega ao professor.

## Trabalhar em dupla

Seu colega pode clonar por ser público. Para escrever diretamente, o proprietário precisa adicioná-lo em Settings → Collaborators. Sem convite, ele pode usar fork e pull request.

```bash
git checkout -b feat/minha-melhoria
# faça alterações
git add .
git commit -m "Descreve a alteração"
git push -u origin feat/minha-melhoria
```

Uma divisão possível: pessoa A cuida do pipeline, schema e armazenamento; pessoa B coleta as imagens, confere resultados e prepara análise/apresentação. Ambos devem testar o fluxo ao vivo.

## Testes

```bash
pytest -q
```

Os testes usam respostas de IA simuladas para serem reproduzíveis e não consumir créditos. Eles exercitam o Prefect real, a validação Great Expectations real e o SQLite real. Testes da API Gemini exigem uma chave válida e imagens reais.

## Entrega acadêmica

- [Arquitetura, decisões e métricas](docs/arquitetura.md)
- [Dicionário de dados](docs/dicionario.md)
- [Relatório e protocolo de avaliação](docs/relatorio.md)
- [Roteiro da apresentação e demonstração](docs/apresentacao.md)

## Limitações

Uma regra de plausibilidade não detecta todo erro de leitura: R$ 29 pode ser lido como R$ 79 e continuar válido. A avaliação de acurácia exige conferência manual. Moeda ausente permanece nula. Preços por tamanho viram itens separados. Não atribuímos uma categoria que não esteja no cardápio. O máximo razoável deve ser ajustado por moeda e tipo de cardápio. Menus vazios ficam para revisão, com métricas de itens indefinidas.

A latência começa quando o backend recebe os bytes e inclui preparação, inferência, validação e commit, mas não o tempo de rede do navegador até o servidor. Falhas são contabilizadas separadamente. Custos de chamadas que falham sem retornar uso são desconhecidos. Para apresentar gasto total faturado, confronte o painel do provedor.

## Referências

- DoorDash: https://careersatdoordash.com/blog/doordash-llm-transcribe-menu/
- ByteByteGo: https://blog.bytebytego.com/p/how-doordash-uses-ai-models-to-understand
- Prefect: https://docs.prefect.io/v3/concepts/tasks
- Great Expectations: https://docs.greatexpectations.io/docs/core/connect_to_data/dataframes/
- Gemini: https://ai.google.dev/gemini-api/docs/structured-output

Código disponível sob licença MIT. Imagens de terceiros mantêm suas próprias licenças e atribuições.
