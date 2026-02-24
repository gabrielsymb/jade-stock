# Contrato de Eventos (Base)

## 1. Objetivo

Padronizar eventos de domínio para integração entre módulos e futura implementação de API/event-driven.

## 2. Padrão mínimo de evento

Campos obrigatórios:

- `event_name`
- `event_id`
- `occurred_at`
- `actor_id`
- `tenant_id`
- `correlation_id`
- `payload`

## 3. Eventos iniciais do domínio

### 3.1 Recebimento

- `recebimento_conferido`
- `recebimento_divergente`

### 3.2 Avarias

- `avaria_registrada`
- `avaria_aprovada`

### 3.3 Inventário cíclico

- `contagem_iniciada`
- `contagem_confirmada`
- `divergencia_identificada`

### 3.4 Reposição e compra

- `reposicao_sugerida`
- `compra_aprovada`
- `compra_rejeitada`

### 3.5 Movimentacao de estoque

- `movimentacao_estoque_registrada`
- `ajuste_estoque_registrado`

## 4. Regras de Governança de Evento

- Nenhum evento pode ser emitido sem `correlation_id`.
- Eventos críticos devem ser idempotentes no consumidor.
- Eventos devem ter versionamento de payload (`schema_version`).

## 5. Exemplo de payload (conceitual)

```json
{
  "event_name": "contagem_confirmada",
  "event_id": "evt_123",
  "occurred_at": "2026-02-21T12:00:00Z",
  "actor_id": "op_42",
  "tenant_id": "lojax",
  "correlation_id": "cnt_20260221_001",
  "schema_version": "1.0",
  "payload": {
    "item_id": "sku_1",
    "endereco": "frente",
    "saldo_anterior": 20,
    "saldo_contado": 18
  }
}
```
