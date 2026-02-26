# Jade-stock

Sistema integrado de gestão empresarial com foco atual no módulo WMS.

## Estado atual (26/02/2026)

- API WMS pronta para deploy técnico local.
- Suite de testes validada no ambiente atual: `140 passed, 5 skipped`.
- Módulos `Contabil`, `PDV` e `IA/Analytics` seguem como trilhas de evolução (documentação e desenho), sem pastas placeholder no código-fonte.

## Mapa de documentação (ordem recomendada)

| Documento | Quando ler | O que explica |
|---|---|---|
| [README.md](./README.md) | Primeiro contato | Visão geral, setup e operação rápida |
| [JADE-STOCK-BIBLIA-DO-SISTEMA.md](./JADE-STOCK-BIBLIA-DO-SISTEMA.md) | Entender arquitetura completa | Decisões de arquitetura, módulos e operação |
| [WMS/README.md](./WMS/README.md) | Trabalhar no módulo WMS | Regras, endpoints, scripts e fluxo técnico real |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | Antes de abrir PR/commit | Padrões de contribuição, validações e checklist |
| [DOCS_BOAS_PRACTICES.md](./DOCS_BOAS_PRACTICES.md) | Escrever/atualizar docs | Convenções e governança de documentação |
| [guia_de_estruture.md](./guia_de_estruture.md) | Organizar o repositório | Estrutura de pastas e política de criação de módulos |
| [jade-stock-adendos.docx.md](./jade-stock-adendos.docx.md) | Evoluções futuras | Adendos de XML, PDV e fornecedores com visão de roadmap |

## Setup rápido

```bash
cd Jade-stock
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r WMS/requirements-dev.txt
```

## Subir API WMS

```bash
cd WMS
cp .env.example .env
# Ajuste WMS_POSTGRES_DSN (sync/psycopg2) e DATABASE_URL (async/alembic/xml)

# Modo em memória (dev)
WMS_API_BACKEND=inmemory ./scripts/run_api.sh

# Modo PostgreSQL
WMS_API_BACKEND=postgres ./scripts/run_api.sh
```

Health check:

```bash
curl http://127.0.0.1:8000/v1/health
```

## Testes e gate

```bash
cd WMS
source ../.venv/bin/activate

# Suite principal
pytest -q -rs

# Trava de release
./scripts/release_gate_enhanced.sh
```

## Política de commit (resumo)

- Não criar/commitar pastas vazias de módulos futuros.
- Separar staging por escopo (`git add -p`), evitando misturar:
  - núcleo WMS pronto para deploy;
  - material experimental/legado em evolução.

## Status dos módulos

| Módulo | Status | Implementação |
|---|---|---|
| WMS | Ativo | Código + testes + scripts de deploy |
| Contábil | Planejado | Documentação e desenho |
| PDV | Planejado | Documentação em adendos |
| IA/Analytics | Planejado | Documentação e estratégia de evolução |
