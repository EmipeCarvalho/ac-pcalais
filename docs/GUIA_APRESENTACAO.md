# Guia de apresentação do extrator de cardápios

Revisão do enunciado de Pedro Calais e da versão principal do repositório em 11/11/2026. Roteiro pensado para aproximadamente 10 a 12 minutos, ajustável ao tempo que o professor conceder. O objetivo é explicar as decisões e demonstrar evidências, sem decorar código.

## Conferência do trabalho

| Critério do professor | Peso | Evidência atual | Atenção antes da apresentação |
|---|---|---|---|
| Apresentação da solução e arquitetura | 20% | Interface e pipeline implementados | Ensaiar este roteiro e preparar as telas que serão abertas |
| Código Python com Prefect e interface | 20% | Cinco tasks, um flow, logs e Streamlit | Abrir o arquivo flow.py e mostrar as etapas em ordem |
| CSV ou SQLite com dicionário | 20% | CSV do lote com 1.289 linhas, 50 execuções e dicionário | Extrair o ZIP do lote; o output padrão ainda contém dez execuções históricas |
| Avaliação e relatório | 20% | Cinquenta imagens, fontes, hashes, quatro métricas e análise | Explicar denominadores, revalidação e limites da amostra |
| Execução ao vivo | 20% | Upload dispara o pipeline real | Ensaiar no computador da apresentação com chave, internet e uma foto inédita |

O PR 1 foi incorporado à main. Não confundir a main deste repositório com a versão original do repositório do Gabriel. Não há evidência de que o merge tenha atualizado o repositório dele.

### O que está pendente ou merece cuidado

1. A demonstração no computador da dupla ainda precisa ser ensaiada. Testes anteriores não garantem rede, saldo de API ou instalação nesse computador.
2. O aplicativo abre os dez resultados históricos em output por padrão. O lote final está em reports/avaliacao_50/resultados_completos.zip. Abra o relatório e o CSV desse lote separadamente para mostrar os resultados de cinquenta imagens. Não apresente a tela dos dez registros como se fosse o lote final.
3. Os treze cardápios sinalizados não foram todos conferidos manualmente. A atividade exige discutir falhas, não esconder resultados ruins. O relatório já descreve casos; confira exemplos para conseguir explicá-los.
4. O resultado de 98,84% é plausibilidade de preços, não acurácia de transcrição. O resultado de 37 aprovados significa aprovação nas regras configuradas, não garantia de que todos os textos estão corretos.
5. O teto de preço 1 a 1.500 é aplicado na moeda original, embora a amostra tenha várias moedas. É uma simplificação da POC.
6. O schema pede moeda como texto e pode induzir inferência quando a moeda não está visível. Na auditoria do CSV, há 33 linhas com moeda vazia. A taxa de missing divulgada considera apenas categoria, nome e preço. Não diga que mede todos os campos do sistema.
7. A revalidação de moedas aconteceu offline. A latência média original foi 18,694 s; a latência contabilizando essa etapa adicional foi 18,814 s. O tempo total concorrente original foi 272,8 s. Essas medidas não são intercambiáveis.

Não há exigência explícita de usar PowerPoint, hospedar um site ou treinar um modelo. O professor exige apresentação, interface, pipeline, dados, relatório e demonstração ao vivo. O projeto escolhe CSV e a abordagem multimodal, opções permitidas pelo enunciado.

## Parte 1 Apresentação da solução e arquitetura

Tempo sugerido de fala: 1 a 2 minutos. Na tela: página inicial e diagrama do fluxo.

### Fala sugerida

“Nosso trabalho é uma prova de conceito para transformar fotos de cardápios em dados organizados. Na foto, os produtos e preços estão espalhados pelo layout. A proposta é extrair essa informação, verificar problemas e guardar o resultado em uma tabela que possa ser analisada depois.

O enunciado permitia usar OCR seguido de um modelo de linguagem ou usar um modelo multimodal diretamente. Nós escolhemos a segunda abordagem, com GPT-5 mini. Ele recebe a imagem e as instruções de extração e devolve uma estrutura com categorias, produtos, descrições, preços e variações.

Não treinamos um modelo novo. Usamos um modelo pré-treinado por API e construímos o sistema ao redor dele: preparação da imagem, instruções, organização da resposta, validação e armazenamento.

A sequência é receber a imagem, preparar a foto, extrair com o modelo, normalizar os dados, validar com Great Expectations e salvar em CSV. O Prefect organiza a execução dessas etapas. A interface em Streamlit permite que a pessoa use o fluxo sem escrever comandos.”

## Parte 2 Código do pipeline e orquestração

Tempo sugerido: 2 a 3 minutos. Na tela: backend/pipeline/flow.py, extractor.py e schemas.py.

### Fala sugerida

“No código, o flow é o processo completo e cada task representa uma etapa desse processo. Criamos cinco tasks: pré-processar a imagem, extrair com o modelo multimodal, estruturar e normalizar, validar com Great Expectations e persistir em CSV.

A preparação corrige a orientação de fotos de celular, converte para RGB e limita o maior lado a 2.000 pixels. Isso padroniza a entrada, embora reduzir demais uma imagem também possa dificultar a leitura de letras pequenas.

Na extração, enviamos a foto e um prompt que pede fidelidade ao conteúdo visível. O prompt orienta a não inventar preços e a usar nulo quando o preço não puder ser lido. Também pede que o modelo respeite colunas e categorias e identifique opções de tamanho ou porção.

Usamos saída estruturada com um schema Pydantic. O schema define o formato esperado da resposta. Isso facilita transformar o JSON em tabela, mas não garante que o conteúdo transcrito esteja correto. A verificação do conteúdo é outra etapa.

Na estruturação, limpamos espaços e transformamos a hierarquia de categorias e itens em linhas. Um produto com tamanhos diferentes e preços próprios gera uma linha por variante. Por isso, nosso total de 1.289 representa itens e variantes.

O Prefect controla a ordem, registra as tarefas e produz logs. Desativamos retries automáticos tanto no SDK quanto na tarefa de extração para não multiplicar chamadas sem perceber. Isso é uma escolha de controle de custo, não uma limitação do Prefect.

Os guardrails verificam os dados gerados. Por exemplo, se o preço é positivo, se faltam campos obrigatórios, se existem possíveis duplicatas, se o texto parece um nome válido e se o código da moeda existe. Existem quinze expectativas na suíte. Um resultado só é aprovado se atingir o limiar geral e também passar pelas regras essenciais. Uma falha importante não pode ser compensada por várias regras simples aprovadas.”

### Explicação curta do ETL

Extração: ler a imagem com IA. Transformação: organizar e normalizar a resposta. Carga: guardar as linhas no CSV. A validação integra o fluxo antes da carga. O sistema persiste também resultados sinalizados, com flags e status, para auditoria e revisão.

## Parte 3 CSV resultante e dicionário de dados

Tempo sugerido: 1 a 2 minutos. Na tela: CSV extraído do ZIP e docs/DICIONARIO_DE_DADOS.md.

### Fala sugerida

“Escolhemos CSV, que era uma das alternativas permitidas, em vez de SQLite. Os arquivos são atualizados por append: cada processamento acrescenta registros ao conjunto existente.

O arquivo de itens guarda categoria, nome, descrição, variação, preço, moeda, atributos e alertas de qualidade. O arquivo de execuções guarda o identificador do processamento, origem, status, tempo, modelo, tokens e custo.

O run_id permite relacionar cada item à execução que o gerou. Também registramos o SHA-256 dos bytes da imagem para identificar arquivos repetidos e retomar lotes por conteúdo, não apenas pelo nome. O hash detecta cópias idênticas; não é um detector universal de imagens visualmente semelhantes.

O dicionário explica o significado, o tipo e a obrigatoriedade das colunas. Neste lote, os dados brutos e as verificações foram preservados mesmo quando havia problemas. Marcar para revisão não significa apagar o resultado.”

## Parte 4 Avaliação e relatório de qualidade

Tempo sugerido: 3 minutos. Na tela: reports/avaliacao_50/RELATORIO_50.md.

### Fala sugerida

“Executamos cinquenta imagens distintas obtidas de um dataset público de cardápios. As fontes e os hashes estão no manifesto. A amostra inclui layouts e idiomas diferentes, mas é de conveniência e não representa estatisticamente restaurantes brasileiros.

As cinquenta imagens passaram pelo pipeline sem falhas de API. Extraímos 1.289 linhas de itens e variantes. Depois da validação final, trinta e sete cardápios ficaram aprovados e treze foram sinalizados para revisão. Um desses treze não gerou nenhum item.

A primeira métrica obrigatória é missing data. Definimos categoria, nome e preço como campos obrigatórios para esse indicador. Foram quatorze células ausentes em 3.867 células avaliadas, o que dá aproximadamente 0,36%. Esses quatorze campos ausentes eram preços.

A segunda métrica é a proporção de itens com preços razoáveis. Usamos a faixa de um a mil e quinhentos na moeda original. Dos 1.289 itens, quatorze não tinham preço e um estava fora da faixa. Assim, 1.274 tinham preço preenchido e dentro do intervalo, o que corresponde a 98,84%. Esse número não significa 98,84% de acerto na leitura.

Na latência, a média original por imagem foi cerca de 18,69 segundos, incluindo a persistência dos dados. Como fizemos uma revalidação adicional de moedas, também documentamos a média de 18,81 segundos somando essa etapa local. O lote original levou quatro minutos e trinta e três segundos porque processamos quatro flows concorrentemente. O tempo total não é cinquenta vezes a média quando há paralelismo.

A quarta métrica é custo. Registramos tokens de entrada e saída reportados pela API e multiplicamos pelas tarifas configuradas. O custo estimado do lote foi de aproximadamente 0,1733 dólar, com média de 0,003466 dólar por imagem. É uma estimativa de consumo, não uma conferência da fatura do provedor.

O próprio teste revelou um problema na nossa validação: a lista inicial de moedas rejeitava rupias indianas. Corrigimos a regra para consultar os códigos ISO por pycountry e reaplicamos os guardrails às respostas salvas, sem pagar por novas extrações. A auditoria conserva as verificações anteriores e posteriores.

Também documentamos limitações. Um cardápio com texto pequeno em devanágari retornou zero itens e foi encaminhado para revisão. Um preço pode ser plausível e ainda estar transcrito errado. E itens inteiramente omitidos não entram na nossa taxa de missing por campo. Por isso não afirmamos acurácia total nem eliminamos a necessidade de conferência humana.”

## Parte 5 Demonstração ao vivo

Tempo variável, incluindo a espera pela API. Na tela: aplicativo real, registros de execução e CSV.

### Antes de começar

Usar a main atual do repositório EmipeCarvalho/ac-pcalais. Instalar as dependências no computador da dupla. Configurar a chave apenas no backend/.env local. Testar acesso à internet e disponibilidade da API. Abrir o app e o relatório do lote antes de apresentar. Se for mostrar a UI do Prefect, iniciar o servidor e configurar sua URL antes de iniciar o aplicativo.

Não é necessário hospedar o Streamlit para cumprir o enunciado: ele pode rodar no computador da apresentação. Não mostrar o arquivo .env na tela compartilhada.

### Fala e sequência sugeridas

“Agora vamos usar uma foto escolhida para a demonstração. Ao enviar e clicar em transcrever, a interface aciona o flow do Prefect. Vamos acompanhar as etapas e depois conferir a saída.”

1. Carregar a imagem escolhida pelo professor.
2. Clicar em transcrever e mostrar as etapas.
3. Conferir se os produtos, as categorias e os preços correspondem à foto.
4. Abrir a aba de verificações e explicar pelo menos uma regra.
5. Mostrar o JSON e a tabela, destacando que são duas representações da mesma extração.
6. Baixar o CSV e mostrar o novo run_id no histórico.
7. Se houver resultado sinalizado, explicar a causa. Não refazer escondido apenas para conseguir um resultado aprovado.

“Este é o comportamento esperado de uma prova de conceito: produzir uma estrutura útil, registrar a execução e indicar quando o resultado merece revisão. Se a imagem não permitir uma leitura confiável, a sinalização faz parte da solução.”

Se a API falhar, mostrar o erro e o registro da tentativa. Resultados anteriores podem demonstrar a interface se o professor permitir, mas devem ser identificados como anteriores, sem dizer que acabaram de ser processados.

## Minha participação na dupla

Adaptar somente ao que realmente aconteceu:

“O Gabriel desenvolveu a base inicial. Na revisão e complementação, trabalhamos nas regras de aprovação, nos casos vazios e de erro da interface, na medição de tempo e custo, na identificação das imagens por hash e na avaliação de cinquenta cardápios. Também refinamos o visual e organizamos o relatório. Usamos apoio de IA no desenvolvimento e na revisão. Eu preciso conseguir explicar e demonstrar as decisões do projeto.”

Não dizer que programou tudo sozinho ou que treinou a IA. Se o professor perguntar sobre ferramentas de apoio, responder com transparência.

## Perguntas que podem aparecer

**Por que não usaram OCR separado?** O enunciado permitia modelo multimodal direto. Ele recebe a imagem e considera o texto e a organização visual no mesmo passo. Não fizemos comparação experimental que comprove superioridade sobre OCR.

**Qual é a diferença entre Pydantic e Great Expectations?** Pydantic define a estrutura da resposta. Great Expectations verifica regras de qualidade nos dados estruturados. Um JSON bem formado ainda pode conter um preço errado.

**Por que 13 revisões se a API não falhou?** Falha técnica e problema de qualidade são diferentes. Uma chamada pode responder corretamente como serviço e ainda gerar dados incompletos ou inconsistentes.

**Como 98,84% dos preços são razoáveis e só 74% dos cardápios passaram?** Um indicador avalia linhas de itens; o status avalia o cardápio e considera outras regras. Um único problema essencial pode sinalizar um cardápio inteiro.

**Missing baixo significa que todos os produtos foram extraídos?** Não. A métrica considera campos dos itens que apareceram na saída. Produtos completamente omitidos exigem comparação com a imagem.

**Revisão humana já foi implementada como editor?** Existe sinalização e preservação da auditoria para conferência. Não há um fluxo completo de edição, aprovação e nova validação dentro da interface.

**Por que aprovar um preço até 1.500?** É um limite configurável de plausibilidade, não uma regra universal. O uso de moedas diferentes limita essa escolha; uma evolução seria configurar faixas por moeda e tipo de estabelecimento.

**Treinaram ou fizeram fine tuning?** Não. Usamos inferência de um modelo pré-treinado por API. Não usamos RAG nem uma base vetorial neste pipeline.

**O que melhorariam?** Limites por moeda, representação explícita de moeda desconhecida, validação de moeda ausente, comparação com dados anotados, maior controle de revisão humana e tratamento de fotos muito pequenas.

## Arquivos para deixar abertos

- backend/app.py ou a interface já em execução.
- backend/pipeline/flow.py.
- backend/pipeline/validation.py.
- backend/pipeline/schemas.py.
- docs/DICIONARIO_DE_DADOS.md.
- reports/avaliacao_50/RELATORIO_50.md.
- CSV de itens e execuções extraído do ZIP do lote final.

Se houver slides, uma sequência simples é: problema e arquitetura; cinco tasks; schema e guardrails; persistência; amostra e quatro métricas; falhas e limitações; demonstração. Não existe exigência explícita de quantidade de slides no enunciado.
