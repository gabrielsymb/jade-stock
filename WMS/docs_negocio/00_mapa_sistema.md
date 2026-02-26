# Mapa do Sistema WMS (visão de negócio)

> Atualizado em 26/02/2026.

## O que este sistema é

Este WMS é um sistema para manter o estoque confiável no dia a dia da operação.

Ele foi desenhado para responder perguntas de negócio como:

- O que entrou?
- O que saiu?
- Onde está cada SKU?
- O saldo está correto?
- Houve divergência no recebimento?

## O que este sistema não é (ainda)

- Não é um ERP completo.
- Não é um BI/analytics avançado.
- Não é um motor de previsão estatística.

Ele é o núcleo operacional do estoque, com regras claras e rastreabilidade.

## Estado técnico atual (API)

- API principal em `WMS/wms/interfaces/api/app.py`.
- Porta local padrão: `8000` (via `WMS/scripts/run_api.sh`).
- Endpoints núcleo em `/v1/...` (movimentação, ajuste, avaria, recebimento, inventário, kanban, curva, giro, sazonalidade e orçamento).
- Trilha XML em rota dedicada `/wms/v1/xml/...` (análise/validação/confirmação e histórico).
- SDK disponível em `sdk/` para consumir a API sem acesso direto ao banco.

## Como validar rápido no ambiente local

```bash
cd WMS
source ../.venv/bin/activate
./scripts/run_api.sh
curl http://127.0.0.1:8000/v1/health
```

```bash
cd WMS
source ../.venv/bin/activate
pytest -q -rs
./scripts/release_gate_enhanced.sh
```

## Como ler esta documentação

1. Comece pela visão macro (`00`, `01`, `02`).
2. Entenda os endpoints em linguagem de negócio (`03`).
3. Só depois entre nos detalhes técnicos (`04`, `05`).

## Resultado esperado para o dono do produto

Ao terminar a leitura, você deve conseguir:

- validar se a implementação respeita suas regras de negócio;
- questionar decisões técnicas com segurança;
- priorizar próximos casos de uso sem depender de jargão.
