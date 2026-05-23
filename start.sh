#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="${ROOT}/backend"

if [[ ! -d "${BACKEND}/api" ]]; then
  echo "ERRO: pasta backend/api não encontrada em ${BACKEND}" >&2
  exit 1
fi

cd "${BACKEND}"
export PYTHONPATH="${BACKEND}${PYTHONPATH:+:${PYTHONPATH}}"

exec uvicorn api.main:app --host 0.0.0.0 --port "${PORT:?PORT não definido}"
