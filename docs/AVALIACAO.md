# Avaliação real concluída

O lote de 50 imagens distintas foi processado com a API real em 10/11/2026. Os resultados completos e a metodologia estão em [RELATORIO_50.md](../reports/avaliacao_50/RELATORIO_50.md).

- 50 imagens processadas, com hashes verificados e sem falhas de API.
- 1.289 linhas de itens/variantes.
- 37 cardápios aprovados e 13 para revisão após corrigir a lista de moedas.
- Missing de campos obrigatórios: 0,36%.
- Itens com preço razoável: 98,84%.
- Latência média final: 18,814 s por imagem, incluindo revalidação offline.
- Custo estimado do lote: USD 0,173299, com as tarifas informadas na configuração.

## Correção identificada na avaliação

A lista limitada de moedas rejeitava INR e outros códigos ISO válidos. A regra passou a consultar pycountry. Todas as extrações foram revalidadas localmente sem novas chamadas à IA. Os JSONs preservam as verificações originais e finais e os tempos separados.

## Evidências e limites

Os dados reais estão nos CSVs e na auditoria do arquivo [resultados_completos.zip](../reports/avaliacao_50/resultados_completos.zip). O manifesto preserva as fontes. Nenhuma chave API foi incluída.

Aprovação de guardrails não prova fidelidade de transcrição. Um cardápio em devanágari retornou zero itens por baixa legibilidade e ficou em revisão. Campos totalmente omitidos não aparecem na taxa de missing por campo. Há moedas diferentes e o teto de preço foi aplicado na unidade monetária original, sem conversão. A conferência visual pontual e essa limitação estão descritas no relatório.

## Histórico original

Os dez exemplos originais e seus CSVs foram preservados. Não participam deste lote. Seus status e tempos refletem a versão anterior.

## Antes da apresentação

Revisar os 13 cardápios sinalizados comparando-os às fotos; acrescentar exemplos à apresentação; testar o aplicativo com uma imagem inédita. A avaliação quantitativa real dos 50 cardápios já foi executada e não depende mais de resultados simulados.
