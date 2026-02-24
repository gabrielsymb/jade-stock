# SDK Jade-stock (unificado)

SDK unica na raiz do monorepo para integracao de terceiros com as APIs Jade-stock.

Estado atual:
- `WMS`: implementado (cliente completo para rotas v1 mapeadas no projeto).
- `IA`: placeholder.
- `Contabil`: placeholder.

## Uso rapido

```python
from jadestock_sdk import JadeStockClient

client = JadeStockClient(
    base_url="http://127.0.0.1:8000",
    timeout_seconds=10.0,
)

print(client.health())

print(
    client.registrar_movimentacao(
        {
            "sku_id": "SKU-COCA-350",
            "tipo_movimentacao": "entrada",
            "quantidade": 10,
            "endereco_origem": None,
            "endereco_destino": "DEP-A-01",
            "operador": "op_01",
            "correlation_id": "corr_sdk_001",
            "motivo": "Carga inicial",
        }
    )
)
```

## Idempotencia (recomendado)

Para qualquer `POST`, envie sempre `correlation_id` unico por operacao.

Alternativa: gerar automatico pela SDK.

```python
from jadestock_sdk import JadeStockClient

client = JadeStockClient(
    base_url="http://127.0.0.1:8000",
    auto_correlation_id=True,
)
```

Ou gerar manualmente:

```python
from jadestock_sdk import new_correlation_id

corr = new_correlation_id()
```

## Retries para falha de rede

Retries da SDK cobrem indisponibilidade de rede (`URLError`), com backoff linear.

```python
client = JadeStockClient(
    base_url="http://127.0.0.1:8000",
    retries=2,
    retry_backoff_seconds=0.3,
)
```

## Contrato de erro

Erros HTTP e de conectividade levantam `JadeStockSDKError`:
- `status_code`
- `code`
- `message`
- `details`
- `correlation_id`

Exemplo:

```python
from jadestock_sdk import JadeStockClient, JadeStockSDKError

client = JadeStockClient(base_url="http://127.0.0.1:8000")

try:
    client.registrar_movimentacao({...})
except JadeStockSDKError as exc:
    print(exc.status_code, exc.code, exc.message)
```

## Observacao sobre autenticacao

A SDK aceita token bearer quando a API exigir auth:

```python
client = JadeStockClient(
    base_url="http://127.0.0.1:8000",
    bearer_token="SEU_TOKEN",
)
client.set_bearer_token("TOKEN_ATUALIZADO")
```

## Roadmap

- `IAClient`: previsao de demanda e recomendacao operacional.
- `ContabilClient`: lancamentos, conciliacao e DRE.
