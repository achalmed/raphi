#!/usr/bin/env bash
# run.sh — Lanzador de Raphi escritorio
# Sin argumentos abre la aplicación; con argumentos es la CLI del motor (raphi lista, raphi comprimir a.pdf -n…).
# Usa el venv local si existe (creado por install.sh); si no, el python3 del sistema.
set -euo pipefail

DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"

if [[ -x "${DIR}/.venv/bin/python" ]]; then
    PYTHON="${DIR}/.venv/bin/python"
else
    PYTHON="$(command -v python3)"
fi

if [[ $# -gt 0 ]]; then
    # La CLI corre donde está el usuario: sus rutas relativas son las suyas.
    PYTHONPATH="${DIR}${PYTHONPATH:+:$PYTHONPATH}" exec "$PYTHON" -m raphi "$@"
fi
cd "$DIR"
exec "$PYTHON" -m studio
