# SDK Jade-stock

SDK Python unificada para consumir a API Jade-stock com foco em uso rapido.

## Estado atual

- `JadeStockClient` (WMS core): pronto.
- Trilha XML (`/wms/v1/xml/...`): mapeada no cliente.
- `IAClient` e `ContabilClient`: placeholders de evolucao.

## Instalacao (plug-and-play)

```bash
cd Jade-stock
source .venv/bin/activate
pip install -e ./sdk
```

## Quickstart

```python
from jadestock_sdk import JadeStockClient

client = JadeStockClient(base_url="http://127.0.0.1:8000", auto_correlation_id=True)
print(client.health())

resp = client.movimentacao_entrada(
    sku_id="sku_001",
    quantidade=10,
    endereco_destino="DEP-A-01",
    operador="op_01",
)
print(resp)
```

## Configuracao por ambiente

```bash
export JADESTOCK_BASE_URL="http://127.0.0.1:8000"
export JADESTOCK_AUTO_CORRELATION_ID="true"
export JADESTOCK_RETRIES="2"
```

```python
from jadestock_sdk import JadeStockClient

client = JadeStockClient.from_env()
print(client.health())
```

Variaveis suportadas:

- `JADESTOCK_BASE_URL`
- `JADESTOCK_TIMEOUT_SECONDS`
- `JADESTOCK_BEARER_TOKEN`
- `JADESTOCK_RETRIES`
- `JADESTOCK_RETRY_BACKOFF_SECONDS`
- `JADESTOCK_AUTO_CORRELATION_ID`

## Metodos principais (WMS core)

- `health()`
- `registrar_movimentacao(payload)`
- `registrar_ajuste(payload)`
- `registrar_avaria(payload)`
- `registrar_recebimento(payload)`
- `registrar_inventario_ciclico(payload)`
- `registrar_politica_kanban(payload)`
- `processar_curva_abcd(payload)`
- `processar_giro(payload)`
- `processar_sazonalidade(payload)`
- `simular_orcamento(payload)`

## Helpers anti-boilerplate

- `movimentacao_entrada(...)`
- `movimentacao_saida(...)`
- `movimentacao_transferencia(...)`

Esses helpers ja montam o payload base e geram `correlation_id` quando nao informado.

## Trilha XML dedicada

- `analisar_xml(payload)`
- `validar_xml(payload)`
- `confirmar_xml(payload)`
- `historico_importacoes(tenant_id, ...)`
- `estatisticas_importacoes(tenant_id, dias=30)`
- `verificar_status_nfe(tenant_id, chave_acesso)`

Exemplo:

```python
xml_payload = {
    "tenant_id": "8a3f9a8d-7a3c-4f79-b3d1-33f9ed9e7c10",
    "xml_content": "<nfeProc>...</nfeProc>",
}

analise = client.analisar_xml(xml_payload)
print(analise)
```

## Tratamento de erros

Erros HTTP/rede levantam `JadeStockSDKError` com:

- `status_code`
- `code`
- `message`
- `details`
- `correlation_id`

```python
from jadestock_sdk import JadeStockClient, JadeStockSDKError

try:
    client.registrar_movimentacao({"sku_id": "x"})
except JadeStockSDKError as exc:
    print(exc.status_code, exc.code, exc.message)
```
