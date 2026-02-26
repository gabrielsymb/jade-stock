# Fluxos Reais do Dia a Dia

## Fluxo A: Movimentar estoque

Exemplo: transferir produto do depósito para frente de loja.

1. Operador informa SKU, origem, destino, quantidade.
2. Sistema valida:
   - SKU ativo
   - endereços válidos
   - saldo suficiente na origem
3. Sistema aplica a movimentação.
4. Sistema grava histórico da movimentação.
5. Sistema gera evento.

Resultado: saldo atualizado com rastreabilidade.

## Fluxo B: Ajustar estoque

Exemplo: quebra operacional.

1. Operador informa SKU, endereço, quantidade de ajuste e motivo.
2. Sistema valida regras.
3. Sistema aplica ajuste no saldo.
4. Sistema grava movimentação de ajuste.
5. Sistema gera evento de ajuste.

Resultado: estoque corrigido e auditável.

## Fluxo C: Registrar recebimento

Exemplo: entrada de nota fiscal.

1. Operador informa nota, fornecedor e itens.
2. Sistema compara esperado x conferido.
3. Se houver diferença, marca divergência.
4. Atualiza saldo conforme conferido.
5. Grava recebimento e itens.
6. Gera eventos (conferido e, se necessário, divergente).

Resultado: entrada controlada e divergências visíveis.

## Fluxo D: Importar NF-e XML (trilha dedicada)

Exemplo: fornecedor envia XML e o operador confirma a entrada.

1. Operador envia o conteúdo XML para `POST /wms/v1/xml/analisar`.
2. Sistema valida estrutura e classifica itens (`MATCHED`, `AMBIGUOUS`, `NEW`).
3. Operador revisa e decide confirmações.
4. Operador confirma em `POST /wms/v1/xml/confirmar`.
5. Sistema atualiza estoque e registra histórico da importação.

Resultado: recebimento por XML com rastreabilidade e controle de duplicidade.

## Conexão com suas regras de negócio

Cada fluxo acima foi implementado para refletir diretamente:

- acuracidade de saldo;
- controle por endereço;
- motivo obrigatório para exceções;
- rastreabilidade para auditoria e aprendizado operacional.
