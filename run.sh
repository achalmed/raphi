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
# Raphi Studio corre con el Python del sistema (PySide6 y Kirigami de apt); escritorio/__main__.py lo relanza desde el
# .venv diciéndole dónde está el motor y gui_comun (el repo de al lado, si está; si no, el instalado en el .venv).
if [[ -z "${GUI_COMUN_DIR:-}" && -d "${DIR}/../gui-comun/gui_comun" ]]; then
    export GUI_COMUN_DIR="$(cd "${DIR}/../gui-comun" && pwd)"
fi
if [[ $# -eq 0 || "$1" == "escritorio" ]]; then
    [[ "${1:-}" == "escritorio" ]] && shift
    exec "$PYTHON" -m escritorio "$@"            # Raphi Studio (o, si ya está abierto, le manda los archivos); --web, la ventana web
fi
exec "$PYTHON" -m raphi "$@"
