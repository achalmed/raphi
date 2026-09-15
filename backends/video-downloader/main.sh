#!/usr/bin/env bash
# =============================================================================
#  main.sh — Video Downloader v1.0.0
# =============================================================================
#
#  Punto de entrada. Su único rol es orquestar los módulos de lib/:
#    1. Cargar configuración y módulos
#    2. Parsear argumentos CLI
#    3. Inicializar logger
#    4. (Opcional) actualizar yt-dlp y salir
#    5. Validar dependencias y entradas
#    6. Reunir objetivos (URLs + archivo de lotes)
#    7. Construir el array de argumentos de yt-dlp según el modo
#    8. Mostrar configuración y confirmar
#    9. Procesar cada objetivo
#   10. Resumen y post-comando
#
#  La lógica de negocio vive en lib/. main.sh no debería superar ~120 líneas.
#
#  MOTOR     : yt-dlp (+ ffmpeg). Compatible: Kubuntu / Ubuntu / Arch / Archcraft
# =============================================================================

set -euo pipefail

# --- Directorio del script (funciona desde cualquier CWD) ------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Cargar configuración y módulos en orden de dependencia ----------------
source "${SCRIPT_DIR}/config.sh"
source "${SCRIPT_DIR}/lib/logger.sh"
source "${SCRIPT_DIR}/lib/validator.sh"
source "${SCRIPT_DIR}/lib/cli.sh"
source "${SCRIPT_DIR}/lib/options.sh"
source "${SCRIPT_DIR}/lib/clipper.sh"
source "${SCRIPT_DIR}/lib/downloader.sh"
source "${SCRIPT_DIR}/lib/summary.sh"

# --- update_ytdlp() --------------------------------------------------------
# Actualiza yt-dlp a la última versión y termina. Se separa de main para no
# recargar toda la validación de descarga cuando el usuario solo quiere -U.
update_ytdlp() {
    if ! command -v yt-dlp &>/dev/null; then
        log_error "yt-dlp no está instalado; nada que actualizar."
        exit 5
    fi
    log_title "Actualizando yt-dlp..."
    yt-dlp -U || log_warn "No se pudo autoactualizar (quizá instalado vía gestor de paquetes)."
    exit 0
}

# --- main() ----------------------------------------------------------------
main() {
    # --- Cabecera visual ---------------------------------------------------
    echo ""
    echo -e "${CLR_BOLD}${CLR_BLUE}"
    echo "  ╔══════════════════════════════════════════════════════════════════╗"
    echo "  ║        VIDEO DOWNLOADER v1.1.1 — Descargador universal            ║"
    printf "  ║        %-58s║\n" "$(date '+%d/%m/%Y %H:%M:%S')"
    echo "  ╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${CLR_RESET}"

    # --- FASE 1: Parsear argumentos ----------------------------------------
    parse_args "$@"

    # --- FASE 2: Inicializar logger ----------------------------------------
    logger_init "${OPT_VERBOSE}" "${OPT_LOG}" "${LOG_FILE}" "${LOG_MAX_BYTES}"

    # --- FASE 3: Atajo --update (no requiere el resto del flujo) -----------
    [ "${OPT_UPDATE}" = true ] && update_ytdlp

    # --- FASE 4: Validar dependencias y entradas ---------------------------
    validate_dependencies "${OPT_USE_ARIA2}"
    validate_quality "${OPT_QUALITY}"
    validate_cookies "${OPT_COOKIES_FILE}"
    validate_output_dir "${OPT_OUTPUT_DIR}" "${OPT_SIMULATE}"
    if [ -n "${OPT_CLIP}" ]; then
        clip_parse_range "${OPT_CLIP}"
    fi

    # --- FASE 5: Reunir objetivos ------------------------------------------
    collect_targets OPT_URLS "${OPT_BATCH_FILE}"
    validate_targets TARGETS
    for target in "${TARGETS[@]}"; do
        warn_if_not_url "${target}"
    done

    # --- FASE 6: Construir argumentos de yt-dlp según el modo --------------
    if [ "${OPT_MODE}" = "info" ] || [ "${OPT_MODE}" = "formats" ]; then
        build_info_args
    else
        build_ytdlp_args
    fi
    log_debug "Argumentos yt-dlp: ${YTDLP_ARGS[*]}"

    # --- FASE 7: Mostrar configuración y confirmar -------------------------
    print_config_banner "${#TARGETS[@]}"
    confirm_or_abort "${OPT_NO_CONFIRM}" "${OPT_SIMULATE}" "${OPT_MODE}"

    # --- FASE 8: Procesar cada objetivo ------------------------------------
    run_all_targets "${OPT_MODE}" "${OPT_SLEEP}"

    # --- FASE 9: Resumen y post-comando ------------------------------------
    # No usar ${OPT_LOG:+...}: OPT_LOG es la cadena "true"/"false" (nunca vacía)
    local summary_log_path=""
    [ "${OPT_LOG}" = true ] && summary_log_path="${LOG_FILE}"
    show_summary "${DL_OK_COUNT}" "${DL_FAIL_COUNT}" "${OPT_MODE}" "${summary_log_path}"
    run_post_command "${OPT_POST_CMD}" "${OPT_SIMULATE}"

    # Código de salida distinto de 0 si todo falló (útil en scripts/cron)
    [ "${DL_OK_COUNT}" -eq 0 ] && [ "${DL_FAIL_COUNT}" -gt 0 ] && exit 1
    return 0
}

main "$@"
