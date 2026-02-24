#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -f .env ]]; then
  # Exporta variaveis do .env para subprocessos (python unittest).
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if [[ -z "${WMS_POSTGRES_DSN:-}" ]]; then
  echo "Erro: WMS_POSTGRES_DSN nao definido."
  echo "Use .env (copie de .env.example) ou exporte no shell."
  exit 1
fi

echo "Rodando testes SQL (integração) com DSN configurado..."
python3 -m unittest \
  tests.test_postgres_core_integration \
  tests.test_postgres_transactional_behavior \
  -v
