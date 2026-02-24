# Caso de Uso Executavel: RegistrarAjusteEstoque

## 1. Objetivo

Permitir ajuste manual/auditavel de saldo por SKU e endereco, com motivo obrigatorio e evento de dominio.

## 2. Entrada (Input Contract)

- `sku_id`
- `endereco_codigo`
- `quantidade_ajuste` (positivo = incrementa, negativo = reduz)
- `operador`
- `correlation_id`
- `motivo`

## 3. Pre-condicoes

1. SKU ativo.
2. Endereco valido e ativo.
3. Operador autorizado.

## 4. Regras de Negocio

1. Ajuste nao pode ser zero.
2. Motivo e obrigatorio.
3. Ajuste negativo exige saldo suficiente no endereco.
4. Toda alteracao gera historico de movimentacao.
5. Toda execucao emite evento de dominio.

## 5. Saida (Output Contract)

- `movimentacao_id`
- `saldo_atualizado`
- `evento_emitido`

## 6. Evento Obrigatorio

- `ajuste_estoque_registrado`

Payload minimo:

- `movimentacao_id`
- `sku_id`
- `quantidade`
- `endereco_origem`
- `endereco_destino`
- `actor_id`
- `correlation_id`
- `motivo`

## 7. Erros de Dominio

- `quantidade_invalida`
- `motivo_obrigatorio`
- `sku_inativo_ou_inexistente`
- `endereco_invalido`
- `estoque_insuficiente`
