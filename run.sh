#!/usr/bin/env bash
# run.sh — Lanzador de Raphi escritorio
# Sin argumentos (o «escritorio archivos…») abre la ventana; con otros, es la CLI del motor (raphi lista, raphi comprimir a.pdf -n…).
# Usa el venv local si existe (creado por install.sh); si no, el python3 del sistema.
set -euo pipefail

DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"

if [[ -x "${DIR}/.venv/bin/python" ]]; then
    PYTHON="${DIR}/.venv/bin/python"
else
    PYTHON="$(command -v python3)"
fi

# Todo corre donde está el usuario (sus rutas relativas son las suyas); el paquete se encuentra por PYTHONPATH.
export PYTHONPATH="${DIR}${PYTHONPATH:+:$PYTHONPATH}"
if [[ $# -eq 0 || "$1" == "escritorio" ]]; then
    [[ "${1:-}" == "escritorio" ]] && shift
    exec "$PYTHON" -m escritorio "$@"            # la ventana (o, si ya está abierta, le manda los archivos)
fi
exec "$PYTHON" -m raphi "$@"
