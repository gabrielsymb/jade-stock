#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "[release-gate] Iniciando validacao final..."

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if [[ -z "${WMS_POSTGRES_DSN:-}" ]]; then
  echo "[ERRO] WMS_POSTGRES_DSN nao definido."
  exit 1
fi

echo "[1/5] Validando dependencias Python..."
python3 - <<'PY'
mods = ["fastapi", "uvicorn", "httpx", "psycopg2"]
missing = []
for m in mods:
    try:
        __import__(m)
    except Exception:
        missing.append(m)
if missing:
    raise SystemExit(f"Dependencias ausentes: {', '.join(missing)}")
print("Dependencias OK")
PY

echo "[2/5] Validando conexao e tabelas criticas no Postgres..."
python3 - <<'PY'
import os
import psycopg2

required_tables = [
    "sku",
    "endereco",
    "saldo_estoque",
    "movimentacao_estoque",
    "recebimento",
    "recebimento_item",
    "event_store",
    "idempotency_command",
]

conn = psycopg2.connect(os.environ["WMS_POSTGRES_DSN"])
try:
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT tablename
            FROM pg_catalog.pg_tables
            WHERE schemaname = ANY(current_schemas(false))
            """
        )
        existing = {r[0] for r in cur.fetchall()}
    missing = [t for t in required_tables if t not in existing]
    if missing:
        raise SystemExit(f"Tabelas ausentes no schema atual: {', '.join(missing)}")
finally:
    conn.close()

print("Schema core + idempotencia OK")
PY

echo "[3/5] Testes transacionais e SQL core..."
python3 -m unittest \
  tests.test_postgres_core_integration \
  tests.test_postgres_transactional_behavior \
  -v

echo "[4/5] Testes de API Postgres (fluxo + idempotencia)..."
python3 -m unittest \
  tests.test_api_postgres_integration \
  -v

echo "[5/5] Testes de dominio (use cases principais)..."
python3 -m unittest \
  tests.test_registrar_movimentacao_estoque \
  tests.test_registrar_ajuste_estoque \
  tests.test_registrar_avaria_estoque \
  tests.test_registrar_recebimento \
  tests.test_registrar_inventario_ciclico \
  tests.test_processar_curva_abcd \
  tests.test_processar_giro_estoque \
  tests.test_processar_sazonalidade_operacional \
  tests.test_processar_governanca_orcamentaria \
  -v

echo "[release-gate] OK - trava final concluida."
