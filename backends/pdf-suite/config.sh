#!/usr/bin/env bash
# =============================================================================
# config.sh — Configuración centralizada de pdf-suite
# =============================================================================
# NOTA: Este archivo se sourcea desde main.sh y todos los módulos lib/*.sh
# No ejecutar directamente.
# =============================================================================

# -----------------------------------------------------------------------------
# VERSIÓN
# -----------------------------------------------------------------------------
readonly PDF_SUITE_VERSION="3.0.0"
readonly PDF_SUITE_NAME="pdf-suite"

# -----------------------------------------------------------------------------
# RUTAS BASE
# Resuelve la ruta real del proyecto aunque se llame con symlink o wrapper.
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR

LIB_DIR="${SCRIPT_DIR}/lib"
readonly LIB_DIR

# Directorio de trabajo temporal (limpiado automáticamente al salir)
WORK_DIR=""   # se inicializa en main.sh con mktemp

# Directorio de logs persistentes (opcional, se activa con --log-file)
LOG_DIR="${HOME}/.local/share/pdf-suite/logs"

# Directorio de búsqueda de PDFs del usuario
DOCUMENTS_DIR="${DOCS_ROOT:-${HOME}/Documents}"   # FS2: core/env.sh lo fija si está cargado

# -----------------------------------------------------------------------------
# OPCIONES GLOBALES POR DEFECTO
# Todas pueden sobreescribirse con flags CLI o variables de entorno.
# -----------------------------------------------------------------------------
VERBOSE=false
DRY_RUN=false
FORCE=false
RECURSIVE=false
LOG_TO_FILE=false

# Sufijo por defecto para archivos de salida generados por operaciones
# que no reemplazan el original (compress, convert, etc.)
DEFAULT_SUFFIX="_out"

# Umbral mínimo de reducción (%) para aceptar un PDF comprimido
COMPRESS_THRESHOLD=5

# Método de compresión por defecto
COMPRESS_METHOD="ebook"

# Idioma por defecto para OCR
OCR_LANG="spa"

# DPI por defecto para conversión PDF → imagen
RENDER_DPI=150

# Formato por defecto para conversión PDF → imagen
RENDER_FORMAT="png"

# -----------------------------------------------------------------------------
# COLORES ANSI
# Se desactivan automáticamente si la salida no es un terminal (pipes, logs).
# -----------------------------------------------------------------------------
if [[ -t 1 ]]; then
    readonly C_RED='\033[0;31m'
    readonly C_GREEN='\033[0;32m'
    readonly C_YELLOW='\033[1;33m'
    readonly C_BLUE='\033[0;34m'
    readonly C_MAGENTA='\033[0;35m'
    readonly C_CYAN='\033[0;36m'
    readonly C_BOLD='\033[1m'
    readonly C_DIM='\033[2m'
    readonly C_RESET='\033[0m'
else
    readonly C_RED=''
    readonly C_GREEN=''
    readonly C_YELLOW=''
    readonly C_BLUE=''
    readonly C_MAGENTA=''
    readonly C_CYAN=''
    readonly C_BOLD=''
    readonly C_DIM=''
    readonly C_RESET=''
fi

# -----------------------------------------------------------------------------
# SÍMBOLOS DE ESTADO (compatibles con terminales sin nerd fonts)
# -----------------------------------------------------------------------------
readonly SYM_OK="✓"
readonly SYM_FAIL="✗"
readonly SYM_SKIP="⊘"
readonly SYM_WARN="⚠"
readonly SYM_INFO="•"
readonly SYM_RUN="▶"

# -----------------------------------------------------------------------------
# SEPARADORES VISUALES
# -----------------------------------------------------------------------------
readonly SEP_HEAVY="════════════════════════════════════════════════════════════════"
readonly SEP_LIGHT="────────────────────────────────────────────────────────────────"

# -----------------------------------------------------------------------------
# CARPETAS DE BÚSQUEDA CONOCIDAS DEL USUARIO
# El usuario puede agregar más rutas a este array antes de ejecutar el script.
# -----------------------------------------------------------------------------
PDF_SEARCH_PATHS=(
    "${HOME}/Documents/biblioteca"
    "${HOME}/Documents/notas"
    "${HOME}/Documents/datafw"
    "${HOME}/Documents/escritura"
    "${HOME}/Documents/web"
    "${HOME}/Documents/archivo"
    "${HOME}/Documents/doc_administrativos"
    "${HOME}/Documents/doc_cv"
    "${HOME}/Documents/doc_financieros"
    "${HOME}/Documents/pub_actus-mercator"
    "${HOME}/Documents/pub_aequilibria"
    "${HOME}/Documents/pub_axiomata"
    "${HOME}/Documents/pub_chaska"
    "${HOME}/Documents/pub_dialectica-y-mercado"
    "${HOME}/Documents/pub_epsilon-y-beta"
    "${HOME}/Documents/pub_methodica"
    "${HOME}/Documents/pub_numerus-scriptum"
    "${HOME}/Documents/pub_optimums"
    "${HOME}/Documents/pub_pecunia-fluxus"
    "${HOME}/Documents/pub_res-publica"
    "${HOME}/Downloads"
)
