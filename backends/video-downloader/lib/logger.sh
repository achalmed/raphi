#!/usr/bin/env bash
# scripts_for_linux/script_video_downloader/lib/logger.sh — envoltorio (FS2, 2026-09-07): el logger vive en core/shell-lib/logger.sh; aquí solo lo propio de esta suite.
_core_d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; while [ "$_core_d" != / ] && [ ! -f "$_core_d/core/shell-lib/logger.sh" ]; do _core_d="$(dirname "$_core_d")"; done
[ -f "$_core_d/core/shell-lib/logger.sh" ] || { echo "[ERROR] no encuentro core/shell-lib/logger.sh subiendo desde ${BASH_SOURCE[0]}" >&2; exit 1; }
source "$_core_d/core/shell-lib/logger.sh"; unset _core_d

# propio de la suite: logger_init(verbose, log_activo, archivo, max_bytes) con cabecera de sesión (LOGGER_* se conservan para lib/)
LOGGER_VERBOSE=false; LOGGER_LOG_ENABLED=false; LOGGER_LOG_FILE=""
logger_init() {
    LOGGER_VERBOSE="${1:-false}"; LOGGER_LOG_ENABLED="${2:-false}"; LOGGER_LOG_FILE="${3:-}"
    LOG_VERBOSE="$LOGGER_VERBOSE"
    if [ "$LOGGER_LOG_ENABLED" = true ] && [ -n "$LOGGER_LOG_FILE" ]; then
        mkdir -p "$(dirname "$LOGGER_LOG_FILE")" 2>/dev/null || true
        LOG_FILE="$LOGGER_LOG_FILE"; log_rotate_if_needed "$LOG_FILE" "${4:-10485760}"
        { echo "════════════════════════════════════════════════"; echo "  SESIÓN DE DESCARGA: $(date '+%Y-%m-%d %H:%M:%S')"
          echo "  Usuario: ${USER:-desconocido}"; echo "  Host:    $(hostname)"; echo "════════════════════════════════════════════════"; } >> "$LOG_FILE"
    fi
    return 0
}
