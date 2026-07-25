#!/usr/bin/env bash
# =============================================================================
#  lib/summary.sh — Banner de configuración, resumen final y post-comando
# =============================================================================
#
#  Salida orientada al usuario: muestra la configuración antes de descargar
#  (para que pueda confirmar o cancelar) y el balance al terminar. Aislar esto
#  aquí mantiene main.sh centrado en el flujo.
# =============================================================================

# ── print_config_banner() ────────────────────────────────────────────────────
# Resume la configuración activa antes de iniciar. Muestra solo lo relevante
# según el modo para no abrumar.
#
# Arguments:
#   $1 - Número de objetivos a procesar
print_config_banner() {
    local target_count="$1"
    echo ""
    log_title "Configuración de la descarga"
    log_separator
    printf "  %-16s %s\n" "Objetivos:"  "${target_count}"
    printf "  %-16s %s\n" "Modo:"        "${OPT_MODE}"

    case "${OPT_MODE}" in
        audio)
            printf "  %-16s %s (calidad %s)\n" "Audio:" "${OPT_AUDIO_FORMAT}" "${OPT_AUDIO_QUALITY}" ;;
        info|formats)
            : ;;  # estos modos no descargan; el resto de campos no aplica
        *)
            printf "  %-16s %s\n" "Calidad:"   "${OPT_QUALITY}"
            printf "  %-16s %s\n" "Contenedor:" "${OPT_CONTAINER}"
            [ -n "${OPT_FORMAT}" ] && printf "  %-16s %s\n" "Formato -f:" "${OPT_FORMAT}" ;;
    esac

    if [ "${OPT_MODE}" != "info" ] && [ "${OPT_MODE}" != "formats" ]; then
        printf "  %-16s %s\n" "Destino:" "${OPT_OUTPUT_DIR}"
        _banner_flag "Subtítulos"  "${OPT_SUBS}"
        _banner_flag "Miniatura"   "${OPT_EMBED_THUMBNAIL}"
        _banner_flag "SponsorBlock" "${OPT_SPONSORBLOCK}"
        _banner_flag "Archivo hist." "${OPT_ARCHIVE}"
        _banner_flag "aria2c"      "${OPT_USE_ARIA2}"
    fi
    [ -n "${OPT_COOKIES_BROWSER}" ] && printf "  %-16s %s\n" "Cookies:" "navegador ${OPT_COOKIES_BROWSER}"
    [ -n "${OPT_COOKIES_FILE}" ]    && printf "  %-16s %s\n" "Cookies:" "${OPT_COOKIES_FILE}"
    [ "${OPT_SIMULATE}" = true ]    && log_warn "  MODO SIMULACIÓN: no se descargará nada"
    log_separator
}

# ── _banner_flag() ───────────────────────────────────────────────────────────
# Imprime una fila del banner solo si la flag booleana está activa.
#
# Arguments:
#   $1 - Etiqueta a mostrar
#   $2 - Valor booleano (true/false)
_banner_flag() {
    [ "$2" = true ] && printf "  %-16s %s\n" "$1:" "sí"
    return 0
}

# ── confirm_or_abort() ───────────────────────────────────────────────────────
# Pide confirmación interactiva salvo que se pase --no-confirm o --simulate,
# o que el modo sea de solo lectura (info/formats).
#
# Arguments:
#   $1 - no_confirm (true/false)
#   $2 - simulate (true/false)
#   $3 - modo activo
confirm_or_abort() {
    local no_confirm="$1" simulate="$2" mode="$3"
    if [ "${no_confirm}" = true ] || [ "${simulate}" = true ] \
       || [ "${mode}" = "info" ] || [ "${mode}" = "formats" ]; then
        return 0
    fi
    local answer
    read -rp "$(echo -e "${CLR_BOLD}  ¿Iniciar descarga? [s/n]: ${CLR_RESET}")" answer
    answer=$(echo "${answer}" | tr '[:upper:]' '[:lower:]' | tr -d ' ')
    if [[ ! "${answer}" =~ ^(s|si|sí|y|yes)$ ]]; then
        log_warn "Descarga cancelada por el usuario."
        exit 0
    fi
}

# ── show_summary() ───────────────────────────────────────────────────────────
# Balance final: éxitos, fallos, carpeta de destino y log.
#
# Arguments:
#   $1 - ok_count
#   $2 - fail_count
#   $3 - modo activo
#   $4 - ruta del log (vacía si no se usó --log)
show_summary() {
    local ok="$1" fail="$2" mode="$3" log_path="$4"
    echo ""
    log_separator "═" 70
    log_title "  RESUMEN"
    log_separator "═" 70
    log_ok "Objetivos completados: ${ok}"
    [ "${fail}" -gt 0 ] && log_error "Objetivos con fallo: ${fail}" || log_info "Objetivos con fallo: 0"

    if [ "${mode}" != "info" ] && [ "${mode}" != "formats" ]; then
        log_info "Carpeta de destino: ${OPT_OUTPUT_DIR}"
    fi
    [ -n "${log_path}" ] && log_info "Log guardado en: ${log_path}"
    echo ""
}

# ── run_post_command() ───────────────────────────────────────────────────────
# Ejecuta un comando definido por el usuario al terminar (notificaciones, etc.).
# En simulación solo lo muestra. Se usa `bash -c` para respetar la línea tal cual.
#
# Arguments:
#   $1 - Comando a ejecutar (vacío = no hacer nada)
#   $2 - simulate (true/false)
run_post_command() {
    local cmd="$1" simulate="${2:-false}"
    [ -z "${cmd}" ] && return 0
    if [ "${simulate}" = true ]; then
        log_info "[SIMULACIÓN] Post-comando: ${cmd}"
        return 0
    fi
    log_info "Ejecutando post-comando: ${cmd}"
    bash -c "${cmd}" || log_warn "El post-comando terminó con código distinto de 0."
}
