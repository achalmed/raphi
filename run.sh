#!/usr/bin/env bash
# run.sh — Lanzador de Raphi escritorio
# Usa el venv local si existe (creado por install.sh); si no, el python3 del sistema.
set -euo pipefail

DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"

if [[ -x "${DIR}/.venv/bin/python" ]]; then
    PYTHON="${DIR}/.venv/bin/python"
else
    PYTHON="$(command -v python3)"
fi

cd "$DIR"
exec "$PYTHON" -m studio "$@"
