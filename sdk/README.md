# SDK Jade-stock (unificado)

SDK unico na raiz do projeto para consumo das APIs:

- `WMS` (implementado)
- `IA` (placeholder)
- `Contabil` (placeholder)

## Uso rapido

```python
from jadestock_sdk import JadeStockClient

client = JadeStockClient(base_url="http://127.0.0.1:8000")

health = client.health()
print(health)

out = client.registrar_movimentacao(
    {
        "sku_id": "sku_001",
        "tipo_movimentacao": "entrada",
        "quantidade": 10,
        "endereco_origem": None,
        "endereco_destino": "DEP-A-01",
        "operador": "op_01",
        "correlation_id": "corr_sdk_001",
        "motivo": "Carga inicial",
    }
)
print(out)
```

## Contrato de erro

Erros HTTP levantam `JadeStockSDKError` com:

- `status_code`
- `code`
- `message`
- `details`
- `correlation_id`

## Roadmap do SDK

- `IAClient`: endpoints de previsao e recomendacao
- `ContabilClient`: endpoints de lancamentos e conciliacao
