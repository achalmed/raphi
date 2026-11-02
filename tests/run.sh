#!/usr/bin/env bash
# tests/run.sh — corre las pruebas de Raphi Studio (tests/studio) con pytest, con la carpeta temporal en disco y sin caché.
# Uso: tests/run.sh [opciones de pytest]   (p. ej. -k trabajos)
# Las del motor, la CLI, la API y el escritorio web (tests/test_*.py) se corren aparte con el .venv del repo, como dice
# CLAUDE.md (`.venv/bin/python -m pytest -q tests`). La carpeta temporal va a ~/.cache (no a /tmp, que es RAM). Nada toca
# los archivos del usuario: cada prueba parte de los archivos de muestra (escritorio/studio/muestra.py) en un temporal.
# Las pruebas en proceso usan el binding del Python que corre pytest; las de QML y la de humo abren un proceso hijo con
# el Python del sistema (/usr/bin/python3, el del Qt con Kirigami) sin pantalla y con HOME, XDG_CONFIG_HOME y
# XDG_CACHE_HOME temporales. El motor corre, como en la ventana, con el .venv del repo (si no está, lo que lo necesita se salta).
# Nunca descargan de la red ni transcriben.
set -euo pipefail

DIR_REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIR_PRUEBAS="${DIR_REPO}/tests/studio"
BASE_TMP="${XDG_CACHE_HOME:-$HOME/.cache}/pytest/raphi-studio"
mkdir -p "$BASE_TMP"

export PYTHONDONTWRITEBYTECODE=1
export QT_QPA_PLATFORM=offscreen
if [[ -z "${GUI_COMUN_DIR:-}" && -d "${DIR_REPO}/../gui-comun/gui_comun" ]]; then
    export GUI_COMUN_DIR="$(cd "${DIR_REPO}/../gui-comun" && pwd)"
fi
exec python3 -m pytest "$DIR_PRUEBAS" --basetemp "$BASE_TMP" -p no:cacheprovider -q "$@"
