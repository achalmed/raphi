#!/usr/bin/env bash
# lib/commands/cmd_doctor.sh — Comando doctor: diagnóstico de dependencias.

cmd_doctor() {
    log_header "docflow doctor — diagnóstico del sistema"

    local -a required=(pandoc python3 soffice)
    local -a optional=(qpdf gs pdftotext lualatex magick cwebp exiftool
                       ocrmypdf tesseract inotifywait wkhtmltopdf weasyprint)
    local missing_required=0

    log_plain ""
    log_plain "${C_BOLD}Requeridas:${C_RESET}"
    local tool
    for tool in "${required[@]}"; do
        if deps_has "$tool"; then
            log_plain "  ${C_GREEN}✓${C_RESET} $(printf '%-12s' "$tool") $(deps_version "$tool")"
        else
            log_plain "  ${C_RED}✗${C_RESET} $(printf '%-12s' "$tool") FALTA → $(deps_install_hint "$tool")"
            missing_required=1
        fi
    done

    log_plain ""
    log_plain "${C_BOLD}Opcionales (amplían capacidades):${C_RESET}"
    for tool in "${optional[@]}"; do
        if deps_has "$tool"; then
            log_plain "  ${C_GREEN}✓${C_RESET} $(printf '%-12s' "$tool") ${_DEP_ROLES[$tool]:-}"
        else
            log_plain "  ${C_DIM}○${C_RESET} $(printf '%-12s' "$tool") ${_DEP_ROLES[$tool]:-}"
            log_plain "      → $(deps_install_hint "$tool")"
        fi
    done

    log_plain ""
    log_plain "${C_BOLD}Python:${C_RESET}"
    if python3 -c 'import tomllib' 2>/dev/null; then
        log_plain "  ${C_GREEN}✓${C_RESET} tomllib disponible (config.toml soportado)"
    else
        log_plain "  ${C_YELLOW}!${C_RESET} Python < 3.11: config.toml no disponible (se usan defaults)"
    fi

    log_plain ""
    log_plain "${C_BOLD}Entorno:${C_RESET}"
    log_plain "  Gestor de paquetes : $(deps_pkg_manager || echo desconocido)"
    log_plain "  Núcleos (jobs)     : $(nproc 2>/dev/null || echo '?')"
    log_plain "  Config de usuario  : ${DOCFLOW_CONFIG_FILE_DEFAULT} $([[ -f "$DOCFLOW_CONFIG_FILE_DEFAULT" ]] && echo '(existe)' || echo '(no creada — docflow config init)')"
    log_plain "  Caché              : ${DOCFLOW_CACHE_DIR}"
    log_plain "  Sesiones/reportes  : ${DOCFLOW_STATE_DIR}"
    log_plain ""

    (( missing_required )) && exit "$EXIT_MISSING_DEPS"
    log_info "Todo listo: las dependencias requeridas están instaladas."
    exit 0
}
