#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

export WMS_API_BACKEND="${WMS_API_BACKEND:-inmemory}"
export WMS_API_TENANT_ID="${WMS_API_TENANT_ID:-loja_demo}"
export WMS_API_LOG_LEVEL="${WMS_API_LOG_LEVEL:-warning}"
export WMS_API_ACCESS_LOG="${WMS_API_ACCESS_LOG:-false}"
export WMS_API_RELOAD="${WMS_API_RELOAD:-false}"
export WMS_API_HOST="${WMS_API_HOST:-0.0.0.0}"
export WMS_API_PORT="${WMS_API_PORT:-8000}"

echo "Subindo API WMS em http://${WMS_API_HOST}:${WMS_API_PORT} (backend=${WMS_API_BACKEND})"

UVICORN_ARGS=(
  --host "${WMS_API_HOST}"
  --port "${WMS_API_PORT}"
  --log-level "${WMS_API_LOG_LEVEL}"
)

if [[ "${WMS_API_RELOAD}" == "true" ]]; then
  UVICORN_ARGS+=(--reload)
fi

if [[ "${WMS_API_ACCESS_LOG}" != "true" ]]; then
  UVICORN_ARGS+=(--no-access-log)
fi

python3 -m uvicorn wms.interfaces.api.app:app "${UVICORN_ARGS[@]}"
