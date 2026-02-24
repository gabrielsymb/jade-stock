#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "[1/2] Testes unitarios + integracao"
python3 -m unittest discover -s tests -p 'test_*.py' -v

echo "[2/2] Trava final de release"
./scripts/release_gate.sh
