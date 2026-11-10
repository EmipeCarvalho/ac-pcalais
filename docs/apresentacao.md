# Roteiro da apresentação

## 1. Problema

Fotos de cardápios misturam texto, estrutura visual e preços. A transcrição manual exige tempo e pode introduzir erros. A solução transforma essas imagens em tabelas auditáveis.

## 2. Inspiração e abordagem

A atividade usa o caso DoorDash como referência. Escolhemos modelo multimodal para ler diretamente a imagem e produzir JSON estruturado. Explicar os benefícios e a dependência de API.

## 3. Arquitetura

Mostrar o diagrama de docs/arquitetura.md. Abrir o flow no Prefect e identificar cada tarefa. Mostrar a interface Streamlit.

## 4. Dados e qualidade

Explicar o schema e o dicionário. Demonstrar preço negativo, campo nulo, categoria desconhecida e duplicata. Mostrar que dados sinalizados ficam em revisão e continuam na auditoria.

## 5. Experimento

Depois da execução real, apresentar os 50 cardápios, as quatro métricas e exemplos de sucesso/falha. Usar reports/metrics.json. Enquanto não houver execução, informar que os resultados estão pendentes.

## 6. Demonstração ao vivo

Abrir app e Prefect antes da apresentação. Verificar chave, internet e modelo. Enviar uma foto inédita escolhida pelo professor. Conferir os itens e alertas, baixar CSV e mostrar novo registro no SQLite. Usar fotos de reserva apenas se o professor permitir e identificar resultados antigos como antigos.

## 7. Limitações e melhorias

Plausibilidade não prova acurácia. Exibir um erro real observado no lote. Discutir ajuste por moeda, conferência humana e comparação com outra abordagem.

## Checklist da dupla

- Identificar os dois integrantes na apresentação.
- Cada integrante deve conseguir explicar o fluxo e rodar o app.
- Confirmar 50 imagens diferentes processadas e banco povoado.
- Anexar dicionário, relatório e fontes.
- Conferir métricas e não apresentar testes simulados como extração real.
