#!/usr/bin/env bash
# install.sh — Instalador de Raphi escritorio (antes DocFlow Studio)
#
# 1. Crea un entorno virtual local (.venv) e instala PySide6 + dependencias.
# 2. Enlaza el lanzador en ~/.local/bin/raphi.
# 3. Instala la entrada de escritorio (menú de aplicaciones).
# 4. Retira el lanzador y la entrada del nombre anterior (docflow-studio), si existen.
#
# Los backends Bash (docflow, pdf-suite) tienen sus propios instaladores en
# backends/*/install.sh para dependencias del sistema (pandoc, qpdf, gs…);
# este script solo prepara el frontend.
set -euo pipefail

DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
APPS_DIR="${HOME}/.local/share/applications"

# El Python del sistema antes que el de conda: el de Anaconda carga su propia libbrotli (1.0.x), demasiado vieja para
# QtWebEngine, y la ventana del escritorio no abre. RAPHI_PYTHON elige otro a mano.
PYTHON_BASE="${RAPHI_PYTHON:-}"
if [[ -z "$PYTHON_BASE" ]]; then
    for candidato in /usr/bin/python3 "$(command -v python3)"; do
        if [[ -x "$candidato" ]]; then PYTHON_BASE="$candidato"; break; fi
    done
fi
# Un .venv hecho con conda se rehace (es regenerable: todo sale de requirements.txt).
if [[ -f "${DIR}/.venv/pyvenv.cfg" ]] && grep -qi "conda" "${DIR}/.venv/pyvenv.cfg"; then
    echo "==> El .venv anterior es de conda: se rehace con ${PYTHON_BASE}…"
    rm -rf "${DIR}/.venv"
fi

echo "==> Creando entorno virtual (.venv) con ${PYTHON_BASE}…"
"$PYTHON_BASE" -m venv "${DIR}/.venv"
"${DIR}/.venv/bin/python" -m pip install --upgrade pip >/dev/null
"${DIR}/.venv/bin/python" -m pip install -r "${DIR}/requirements.txt"
# Tiqsi (el contrato de la plataforma) desde el espacio de trabajo, si está al lado: la API y el módulo lo usan.
if [[ -f "${DIR}/../tiqsi/pyproject.toml" ]]; then
    "${DIR}/.venv/bin/python" -m pip install -q -e "${DIR}/../tiqsi"
fi

echo "==> Enlazando lanzador en ${BIN_DIR}/raphi…"
mkdir -p "$BIN_DIR"
chmod +x "${DIR}/run.sh"
ln -sf "${DIR}/run.sh" "${BIN_DIR}/raphi"

echo "==> Instalando entrada de escritorio…"
mkdir -p "$APPS_DIR"
cat > "${APPS_DIR}/raphi.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Raphi
Comment=PDF, ofimática y conversión de archivos
Exec=${DIR}/run.sh
Terminal=false
Categories=Office;Utility;
DESKTOP

# El nombre anterior: solo se retira si es un enlace o la entrada que creaba este instalador.
if [[ -L "${BIN_DIR}/docflow-studio" ]]; then
    echo "==> Retirando el lanzador anterior (docflow-studio)…"
    rm -f "${BIN_DIR}/docflow-studio"
fi
if [[ -f "${APPS_DIR}/docflow-studio.desktop" ]] && grep -q '^Name=DocFlow Studio$' "${APPS_DIR}/docflow-studio.desktop"; then
    rm -f "${APPS_DIR}/docflow-studio.desktop"
fi

echo
echo "Listo. Ejecuta 'raphi' (o búscala en el menú de aplicaciones)."
echo "Sugerencia: instala también las dependencias de los backends:"
echo "  ${DIR}/backends/docflow/install.sh"
echo "  ${DIR}/backends/pdf-suite/install.sh"
