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

echo "Subindo API WMS em http://127.0.0.1:8000 (backend=${WMS_API_BACKEND})"
if [[ "${WMS_API_ACCESS_LOG}" == "true" ]]; then
  python3 -m uvicorn wms.interfaces.api.app:app --host 127.0.0.1 --port 8000 --reload --log-level "${WMS_API_LOG_LEVEL}"
else
  python3 -m uvicorn wms.interfaces.api.app:app --host 127.0.0.1 --port 8000 --reload --log-level "${WMS_API_LOG_LEVEL}" --no-access-log
fi
