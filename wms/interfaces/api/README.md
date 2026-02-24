# Interfaces API

Camada de entrada HTTP/REST/gRPC.

Regra:

- API apenas traduz request/response para casos de uso;
- validacao de regra de negocio permanece em dominio/aplicacao;
- sem regra de negocio direta no controller.

Endpoints minimos (fase atual):

- `POST /v1/movimentacoes`
- `POST /v1/ajustes`
- `POST /v1/avarias`
- `POST /v1/recebimentos`
- `POST /v1/inventarios/ciclico`
- `POST /v1/kanban/politicas`
- `POST /v1/curva-abcd/processar`
- `POST /v1/giro/processar`
- `POST /v1/sazonalidade/processar`
- `POST /v1/orcamento/simular`
- `GET /v1/health`

Execucao local:

```bash
cd WMS
./scripts/run_api.sh
```

Logs da API (opcional, via `.env`):

- `WMS_API_LOG_LEVEL=warning`
- `WMS_API_ACCESS_LOG=false`

Exemplos de request:

`POST /v1/movimentacoes`

```json
{
  "sku_id": "sku_001",
  "tipo_movimentacao": "entrada",
  "quantidade": 10,
  "endereco_origem": null,
  "endereco_destino": "DEP-A-01",
  "operador": "op_01",
  "correlation_id": "corr_api_mov_001",
  "motivo": "Carga inicial"
}
```

`POST /v1/ajustes`

```json
{
  "sku_id": "sku_001",
  "endereco_codigo": "DEP-A-01",
  "quantidade_ajuste": -2,
  "operador": "op_01",
  "correlation_id": "corr_api_ajuste_001",
  "motivo": "Quebra operacional"
}
```

`POST /v1/recebimentos`

```json
{
  "nota_fiscal": "NF-API-001",
  "fornecedor_id": "forn_01",
  "itens": [
    {
      "sku_codigo": "sku_001",
      "quantidade_esperada": 8,
      "quantidade_conferida": 7,
      "endereco_destino": "DEP-A-01",
      "classificacao_divergencia": "falta"
    }
  ],
  "operador": "op_01",
  "correlation_id": "corr_api_rec_001"
}
```

`POST /v1/avarias`

```json
{
  "sku_id": "sku_001",
  "endereco_codigo": "DEP-A-01",
  "quantidade_avaria": 2,
  "operador": "op_01",
  "correlation_id": "corr_api_avaria_001",
  "motivo": "Quebra operacional"
}
```

`POST /v1/inventarios/ciclico`

```json
{
  "operador": "op_01",
  "correlation_id": "corr_api_inv_001",
  "motivo": "Contagem ciclica semanal",
  "itens": [
    {
      "sku_id": "sku_001",
      "endereco_codigo": "DEP-A-01",
      "quantidade_contada": 8
    }
  ]
}
```

`POST /v1/kanban/politicas`

```json
{
  "sku_id": "sku_001",
  "elegivel": true,
  "kanban_ativo": true,
  "faixa_atual": "amarela",
  "faixa_verde_min": 20,
  "faixa_amarela_min": 10,
  "faixa_vermelha_min": 5,
  "operador": "op_01",
  "correlation_id": "corr_api_kanban_001",
  "motivo": "Politica inicial"
}
```

`POST /v1/curva-abcd/processar`

```json
{
  "operador": "op_01",
  "correlation_id": "corr_api_abcd_001",
  "itens": [
    {
      "sku_id": "sku_001",
      "impacto_economico": 1000,
      "variabilidade": 0.1,
      "shelf_life_dias": 60,
      "dias_sem_venda": 10,
      "giro_periodo": 12,
      "lead_time_dias": 2
    }
  ]
}
```

`POST /v1/giro/processar`

```json
{
  "operador": "op_01",
  "correlation_id": "corr_api_giro_001",
  "itens": [
    {
      "sku_id": "sku_001",
      "classe_abc": "A",
      "estoque_atual": 100,
      "venda_media_diaria_prevista": 5,
      "total_vendido_periodo": 40,
      "estoque_medio_periodo": 10,
      "ruptura_recorrente": false,
      "lead_time_dias": 2,
      "shelf_life_dias": 60
    }
  ]
}
```

`POST /v1/sazonalidade/processar`

```json
{
  "operador": "op_01",
  "correlation_id": "corr_api_sazo_001",
  "itens": [
    {
      "sku_id": "sku_001",
      "fator_sazonal": 1.2,
      "confianca_modelo": 0.9,
      "janela_analise_meses": 24,
      "mudanca_estrutural": false,
      "origem_motor": "stats_engine",
      "versao_modelo": "v1"
    }
  ]
}
```

`POST /v1/orcamento/simular`

```json
{
  "operador": "op_01",
  "correlation_id": "corr_api_orc_001",
  "periodo_referencia": "2026-02-01",
  "categoria_id": "cat_a",
  "valor_compra_sugerida": 700,
  "orcamento_total_periodo": 1000,
  "orcamento_categoria_periodo": 600,
  "consumo_atual_total": 500,
  "consumo_atual_categoria": 100,
  "aprovacao_excecao": {
    "aprovado_por": "gestor_01",
    "motivo": "Item critico",
    "valor_aprovado": 700
  }
}
```
