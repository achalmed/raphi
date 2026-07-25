#!/usr/bin/env bash
# =============================================================================
#  lib/logger.sh — Sistema de logging centralizado
# =============================================================================
#
#  Todo el output del script pasa por estas funciones para garantizar formato
#  consistente y redirección trivial. WARN y ERROR van a stderr para no
#  contaminar stdout (útil al encadenar en pipes o cron).
#
#  NIVELES:
#    INFO   — Información general del proceso
#    OK     — Operación completada con éxito
#    WARN   — Advertencia (el script continúa)
#    ERROR  — Error (normalmente se aborta tras este)
#    ACTION — Acción interactiva pendiente del usuario
#    TITLE  — Encabezado de sección
#    DEBUG  — Solo visible con --verbose
# =============================================================================

# ── Detección de capacidad de color del terminal ─────────────────────────────
# Se usa tput en vez de secuencias ANSI hardcoded para máxima compatibilidad
# entre terminales (kitty, xterm, konsole, etc.).
_init_colors() {
    if [ -t 1 ] && command -v tput &>/dev/null \
       && tput colors &>/dev/null 2>&1 \
       && [ "$(tput colors)" -ge 8 ]; then
        CLR_RED=$(tput setaf 1)
        CLR_GREEN=$(tput setaf 2)
        CLR_YELLOW=$(tput setaf 3)
        CLR_BLUE=$(tput setaf 4)
        CLR_MAGENTA=$(tput setaf 5)
        CLR_CYAN=$(tput setaf 6)
        CLR_WHITE=$(tput setaf 7)
        CLR_BOLD=$(tput bold)
        CLR_RESET=$(tput sgr0)
    else
        # Sin color: terminales no interactivas, pipes, redirecciones
        CLR_RED="" CLR_GREEN="" CLR_YELLOW="" CLR_BLUE=""
        CLR_MAGENTA="" CLR_CYAN="" CLR_WHITE="" CLR_BOLD="" CLR_RESET=""
    fi
}

# Llamada única al cargar el módulo
_init_colors

# ── Estado del logger (se fija desde logger_init; no modificar a mano) ────────
LOGGER_VERBOSE=false
LOGGER_LOG_ENABLED=false
LOGGER_LOG_FILE=""

# ── log_write() ──────────────────────────────────────────────────────────────
# Imprime un mensaje formateado en consola y opcionalmente en archivo.
#
# Arguments:
#   $1 - Nivel (INFO, OK, WARN, ERROR, ACTION, TITLE, DEBUG)
#   $@ - Texto del mensaje
# Returns:
#   0 siempre (el logging nunca debe abortar el flujo principal)
log_write() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local line="[${timestamp}] [${level}] ${message}"

    # DEBUG solo visible en modo verbose
    if [ "${level}" = "DEBUG" ] && [ "${LOGGER_VERBOSE}" = false ]; then
        return 0
    fi

    case "${level}" in
        INFO)   echo -e "${CLR_CYAN}${line}${CLR_RESET}" ;;
        OK)     echo -e "${CLR_GREEN}${line}${CLR_RESET}" ;;
        WARN)   echo -e "${CLR_YELLOW}${line}${CLR_RESET}" >&2 ;;
        ERROR)  echo -e "${CLR_RED}${line}${CLR_RESET}" >&2 ;;
        ACTION) echo -e "${CLR_MAGENTA}${line}${CLR_RESET}" ;;
        TITLE)  echo -e "${CLR_BOLD}${CLR_BLUE}${line}${CLR_RESET}" ;;
        DEBUG)  echo -e "${CLR_WHITE}${line}${CLR_RESET}" ;;
        *)      echo "${line}" ;;
    esac

    # Escritura en archivo sin secuencias de color, para lectura limpia
    if [ "${LOGGER_LOG_ENABLED}" = true ] && [ -n "${LOGGER_LOG_FILE}" ]; then
        echo "${line}" >> "${LOGGER_LOG_FILE}"
    fi
}

# ── Atajos por nivel (lo que usan todos los demás módulos) ────────────────────
log_info()   { log_write "INFO"   "$@"; }
log_ok()     { log_write "OK"     "$@"; }
log_warn()   { log_write "WARN"   "$@"; }
log_error()  { log_write "ERROR"  "$@"; }
log_action() { log_write "ACTION" "$@"; }
log_title()  { log_write "TITLE"  "$@"; }
log_debug()  { log_write "DEBUG"  "$@"; }

# ── log_separator() ──────────────────────────────────────────────────────────
# Imprime una línea divisoria para delimitar secciones visualmente.
# Se usa expansión ${var// /c} y no `tr` porque tr traduce POR BYTES y
# rompería caracteres UTF-8 multibyte como ─ o ═ (imprimiría mojibake).
#
# Arguments:
#   $1 - Carácter de relleno (default: ─)
#   $2 - Ancho total (default: 70)
log_separator() {
    local char="${1:-─}"
    local width="${2:-70}"
    local line
    printf -v line '%*s' "${width}" ''
    echo "${line// /${char}}"
}

# ── log_rotate_if_needed() ───────────────────────────────────────────────────
# Si el log supera max_bytes, lo archiva con timestamp y arranca uno nuevo.
# Evita que el log crezca sin límite con uso frecuente de --log.
#
# Arguments:
#   $1 - Ruta al archivo de log
#   $2 - Tamaño máximo en bytes antes de rotar
log_rotate_if_needed() {
    local log_path="$1"
    local max_bytes="${2:-10485760}"

    if [ -f "${log_path}" ]; then
        local current_size
        # stat puede fallar en FS exóticos; 0 fuerza a no rotar (comportamiento seguro)
        current_size=$(stat --printf='%s' "${log_path}" 2>/dev/null || echo "0")
        if [ "${current_size}" -gt "${max_bytes}" ]; then
            local backup_path="${log_path}.$(date +%Y%m%d_%H%M%S).bak"
            mv "${log_path}" "${backup_path}"
            log_info "Log anterior archivado: ${backup_path}"
        fi
    fi
}

# ── logger_init() ────────────────────────────────────────────────────────────
# Configura el logger con las opciones elegidas. Se llama una sola vez desde
# main.sh tras parsear los argumentos.
#
# Arguments:
#   $1 - verbose (true/false)
#   $2 - log_enabled (true/false)
#   $3 - log_file (ruta completa)
#   $4 - max_bytes (para rotación)
logger_init() {
    LOGGER_VERBOSE="${1:-false}"
    LOGGER_LOG_ENABLED="${2:-false}"
    LOGGER_LOG_FILE="${3:-}"
    local max_bytes="${4:-10485760}"

    if [ "${LOGGER_LOG_ENABLED}" = true ] && [ -n "${LOGGER_LOG_FILE}" ]; then
        log_rotate_if_needed "${LOGGER_LOG_FILE}" "${max_bytes}"
        {
            echo "════════════════════════════════════════════════"
            echo "  SESIÓN DE DESCARGA: $(date '+%Y-%m-%d %H:%M:%S')"
            echo "  Usuario: ${USER:-desconocido}"
            echo "  Host:    $(hostname)"
            echo "════════════════════════════════════════════════"
        } >> "${LOGGER_LOG_FILE}"
    fi
}
