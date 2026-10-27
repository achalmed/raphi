#!/usr/bin/env bash
# raphi/backends/pdf-suite/lib/logger.sh — envoltorio (FS2, 2026-09-07): el logger vive en core/shell-lib/logger.sh; aquí solo lo propio de esta suite.
_core_d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; while [ "$_core_d" != / ] && [ ! -f "$_core_d/core/shell-lib/logger.sh" ]; do _core_d="$(dirname "$_core_d")"; done
[ -f "$_core_d/core/shell-lib/logger.sh" ] || { echo "[ERROR] no encuentro core/shell-lib/logger.sh subiendo desde ${BASH_SOURCE[0]}" >&2; exit 1; }
source "$_core_d/core/shell-lib/logger.sh"; unset _core_d

# propio de pdf-suite: símbolos y separadores de config.sh, resumen tabulado y archivo de log por sesión
log_step()    { echo -e "\n${C_BOLD}${C_BLUE}${SYM_RUN} $1${C_RESET}"; }
log_success() { echo -e "  ${C_GREEN}${SYM_OK}${C_RESET} $1"; }
log_failure() { echo -e "  ${C_RED}${SYM_FAIL}${C_RESET} $1" >&2; }
log_skip()    { echo -e "  ${C_YELLOW}${SYM_SKIP}${C_RESET} $1"; }
log_section() { echo -e "\n${C_BOLD}${SEP_HEAVY}${C_RESET}"; echo -e "${C_BOLD}  $1${C_RESET}"; echo -e "${C_BOLD}${SEP_LIGHT}${C_RESET}"; }
init_log_file() {
    [[ "${LOG_TO_FILE:-false}" == "true" ]] || return 0
    mkdir -p "$LOG_DIR" || { log_warn "No se pudo crear el directorio de logs: $LOG_DIR"; LOG_TO_FILE=false; return 1; }
    LOG_FILE_PATH="${LOG_DIR}/pdf-suite_$(date '+%Y%m%d_%H%M%S').log"; LOG_FILE="$LOG_FILE_PATH"
    log_debug "Log en archivo: $LOG_FILE_PATH"
}
