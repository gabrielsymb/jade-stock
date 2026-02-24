# Infrastructure Database

Camada de infraestrutura para persistencia.

Status atual:

- `Database/schema_core.sql` definido para os casos de uso implementados;
- `Database/schema_extended.sql` definido para fases futuras;
- adapters Postgres core iniciados em `wms/infrastructure/postgres/`.
- tabela `idempotency_command` no `schema_core` para proteger escrita da API contra duplicidade.

Diretriz:

- banco deve ser derivado do dominio e dos casos de uso;
- evitar criar tabela sem caso de uso associado;
- manter auditoria e idempotencia como requisitos de persistencia.

Teste de integracao SQL (opcional):

1. Copiar `.env.example` para `.env`
2. Subir Postgres local:

```bash
cd WMS
docker compose -f docker-compose.postgres.yml --env-file .env up -d
```

3. Definir `WMS_POSTGRES_DSN` (via `.env`) e executar:

```bash
cd WMS
./scripts/run_sql_tests.sh
```

Trava final de release:

```bash
cd WMS
./scripts/release_gate.sh
```

Arquivo alvo:

- `tests/test_postgres_core_integration.py`
