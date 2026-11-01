#!/usr/bin/env bash
# backends/video-downloader/lib/logger_sin_core.sh — el logger mínimo cuando core/ no está (Raphi instalado fuera del
# espacio de trabajo). Mismos nombres que core/shell-lib/logger.sh; sin colores si la salida no es una terminal.
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
    : "${CLR_RED:=$'\e[31m'}" "${CLR_GREEN:=$'\e[32m'}" "${CLR_YELLOW:=$'\e[33m'}" "${CLR_CYAN:=$'\e[36m'}"
    : "${CLR_BLUE:=$'\e[34m'}" "${CLR_MAGENTA:=$'\e[35m'}" "${CLR_WHITE:=$'\e[37m'}" "${CLR_GRAY:=$'\e[90m'}"
    : "${CLR_BOLD:=$'\e[1m'}" "${CLR_DIM:=$'\e[2m'}" "${CLR_RESET:=$'\e[0m'}"
fi
: "${CLR_RED:=}" "${CLR_GREEN:=}" "${CLR_YELLOW:=}" "${CLR_CYAN:=}" "${CLR_BOLD:=}" "${CLR_DIM:=}" "${CLR_RESET:=}"
: "${CLR_BLUE:=}" "${CLR_MAGENTA:=}" "${CLR_WHITE:=}" "${CLR_GRAY:=}" "${CLR_ACCENT:=$CLR_MAGENTA}"
: "${CLR_INFO:=$CLR_CYAN}" "${CLR_OK:=$CLR_GREEN}" "${CLR_WARN:=$CLR_YELLOW}" "${CLR_ERROR:=$CLR_RED}"
: "${RED:=$CLR_RED}" "${GREEN:=$CLR_GREEN}" "${YELLOW:=$CLR_YELLOW}" "${BOLD:=$CLR_BOLD}" "${NC:=$CLR_RESET}"
_sin_core_log() {   # NIVEL COLOR MENSAJE…
    local nivel="$1" color="$2"; shift 2
    printf '%s[%s]%s %s\n' "$color" "$nivel" "$CLR_RESET" "$*"
    [ -n "${LOG_FILE:-}" ] && printf '[%s] %s %s\n' "$nivel" "$(date '+%F %T')" "$*" >> "$LOG_FILE" 2>/dev/null
    return 0
}
log_info()  { _sin_core_log INFO "$CLR_INFO" "$@"; }
log_ok()    { _sin_core_log OK "$CLR_OK" "$@"; }
log_success() { log_ok "$@"; }
log_warn()  { _sin_core_log WARN "$CLR_WARN" "$@"; }
log_error() { _sin_core_log ERROR "$CLR_ERROR" "$@" >&2; }
log_debug() { [ "${LOG_VERBOSE:-}" = true ] || [ "${OPT_VERBOSE:-}" = true ] || return 0; _sin_core_log DEBUG "$CLR_DIM" "$@"; }
log_title() { printf '\n%s══ %s ══%s\n' "$CLR_BOLD" "$*" "$CLR_RESET"; }
log_section() { log_title "$@"; }
log_separator() { local c="${1:-─}" w="${2:-70}" l; printf -v l '%*s' "$w" ''; printf '%s\n' "${l// /$c}"; }
log_rotate_if_needed() {
    local ruta="$1" max="${2:-10485760}"
    [ -f "$ruta" ] && [ "$(stat -c %s "$ruta" 2>/dev/null || echo 0)" -gt "$max" ] && mv -f "$ruta" "$ruta.1"
    return 0
}
