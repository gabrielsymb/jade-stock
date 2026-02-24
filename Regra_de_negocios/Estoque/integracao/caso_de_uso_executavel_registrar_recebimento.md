# Caso de Uso Executavel: RegistrarRecebimento

## 1. Objetivo

Formalizar um contrato de aplicacao para o fluxo de recebimento com conferencia, sem dependencia de tecnologia especifica.

## 2. Entrada (Input Contract)

- `nota_fiscal`: identificacao da nota, fornecedor e data.
- `itens`: lista de itens recebidos (`sku_codigo`, quantidade esperada, quantidade conferida, endereco destino).
- `operador`: usuario responsavel pela conferencia.
- `correlation_id`: id de rastreio da operacao.

## 3. Pre-condicoes

1. Nota fiscal valida e nao processada anteriormente.
2. Operador autenticado e autorizado para recebimento.
3. SKU existente e ativo para todos os itens.
4. Endereco de destino valido e ativo.

## 4. Regras de Negocio (Deterministicas)

1. Validar SKU ativo antes de qualquer atualizacao de saldo.
2. Validar endereco de destino por item.
3. Comparar `quantidade_esperada` x `quantidade_conferida`.
4. Em caso de divergencia, classificar por item: `ok`, `falta`, `sobra`, `avaria`.
5. Se houver avaria, exigir motivo e direcionar saldo para tipo de endereco bloqueado/avariado.
6. Toda alteracao de saldo deve gerar historico de movimentacao.
7. O caso de uso deve ser idempotente por `nota_fiscal` + `correlation_id`.

## 5. Saida (Output Contract)

- `recebimento_id`
- `status`: `conferido` ou `conferido_com_divergencia`
- `itens_processados`
- `itens_com_divergencia`
- `saldo_atualizado`: indicador de sucesso
- `eventos_emitidos`

## 6. Evento Obrigatorio

Evento principal:

- `recebimento_conferido`

Payload minimo:

- `recebimento_id`
- `nota_fiscal`
- `itens`
- `divergencias`
- `operador`
- `timestamp`
- `correlation_id`

## 7. Erros de Dominio

- `nota_fiscal_duplicada`
- `sku_inativo_ou_inexistente`
- `endereco_invalido`
- `divergencia_nao_classificada`
- `operador_nao_autorizado`

## 8. Auditoria

Campos minimos de auditoria:

- `created_at`
- `created_by`
- `correlation_id`
- `motivo_ajuste` (quando houver)

## 9. KPI Vinculado

- `divergencia_no_recebimento`
- `tempo_medio_de_conferencia`
- `percentual_de_notas_sem_divergencia`
