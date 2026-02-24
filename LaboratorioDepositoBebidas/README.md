# Laboratorio Deposito de Bebidas

Frontend fake para validar, na pratica, se a API do Jade-stock esta respondendo do jeito esperado.

## O que este laboratorio faz

- Interface visual para testar os metodos do SDK.
- Backend local usando `jadestock_sdk.client.JadeStockClient`.
- Chamadas reais para endpoints `/v1/*` da API WMS.
- Templates prontos de payload para acelerar estudo e teste.

## Estrutura

- `LaboratorioDepositoBebidas/app.py`: backend do laboratorio (FastAPI).
- `LaboratorioDepositoBebidas/static/index.html`: frontend visual.

## Pre-requisitos

- API WMS rodando (porta padrao `8000`):

```bash
cd ~/meus_projetos/Jade-stock/WMS
set -a
source .env
set +a
PYTHONPATH="$PWD" python3 -m uvicorn wms.interfaces.api.app:app --reload --port 8000
```

- Ambiente Python com `fastapi` e `uvicorn` (ja usado no projeto WMS).

## Rodar o laboratorio

```bash
cd ~/meus_projetos/Jade-stock
source .venv/bin/activate
PYTHONPATH=. python3 -m uvicorn LaboratorioDepositoBebidas.app:app --reload --port 8700
```

Abrir no navegador:

- `http://127.0.0.1:8700`

## Como usar

1. Confirmar `Base URL` (normalmente `http://127.0.0.1:8000`).
2. Escolher a operacao do SDK.
3. Carregar template de payload.
4. Clicar em `Executar chamada via SDK`.
5. Ler resposta JSON no painel da direita.

## Observacoes

- Se usar autenticacao no futuro, preencher `Bearer token` no laboratorio.
- Para evitar erro de idempotencia, mude o `correlation_id` quando quiser nova operacao.
- O laboratorio nao substitui testes automatizados; ele complementa com validacao visual.
