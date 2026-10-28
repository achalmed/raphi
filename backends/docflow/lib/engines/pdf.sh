#!/usr/bin/env bash
# lib/engines/pdf.sh — PDF Engine (conversión a PDF).
# Selecciona automáticamente el mejor motor disponible por tipo de documento:
#   · Office/ODF → LibreOffice headless (máxima fidelidad de layout)
#   · Markdown/LaTeX/HTML → pandoc con el mejor --pdf-engine presente
#     (lualatex → wkhtmltopdf → weasyprint), con fallback a LibreOffice
# Post-proceso opcional: PDF/A (ghostscript) y compresión.
# Las operaciones sobre PDFs existentes viven en pdf_ops.sh.

engine_pdf_output_ext() {
    local strategy="${REG_PDF_STRATEGY[$1]:-none}"
    [[ "$strategy" == "none" ]] && return 0
    printf 'pdf'
}

engine_pdf_convert() {
    local input="$1" output="$2"
    local ext strategy
    ext="$(util_ext "$input")"
    strategy="${REG_PDF_STRATEGY[$ext]}"

    # Selección de motor: --pdf-engine fuerza uno; "auto" respeta la estrategia
    local engine="${DOCFLOW_PDF_ENGINE:-auto}"
    if [[ "$engine" == "auto" ]]; then
        case "$strategy" in
            soffice)        engine="soffice" ;;
            pandoc)         engine="pandoc" ;;
            pandoc_soffice) engine="pandoc" ;;
        esac
    fi

    case "$engine" in
        soffice)     _pdf_via_soffice "$input" "$output" ;;
        pandoc)      _pdf_via_pandoc "$input" "$output" \
                         || { [[ "$strategy" == "pandoc_soffice" || "$strategy" == "soffice" ]] \
                              && _pdf_via_soffice "$input" "$output"; } ;;
        wkhtmltopdf) _pdf_via_wkhtmltopdf "$input" "$output" ;;
        weasyprint)  _pdf_via_weasyprint "$input" "$output" ;;
        *) log_error "Motor PDF desconocido: $engine"; return 1 ;;
    esac || return 1

    _pdf_postprocess "$output"
}

_pdf_via_soffice() {
    local input="$1" output="$2"
    deps_require soffice
    local out_dir tmp_out
    out_dir="$(dirname -- "$output")"
    soffice_convert "$input" "pdf" "$out_dir" || return 1
    # soffice nombra la salida según la entrada; renombrar si difiere
    tmp_out="${out_dir}/$(util_basename_noext "$input").pdf"
    [[ "$tmp_out" != "$output" && -f "$tmp_out" ]] && mv -- "$tmp_out" "$output"
    [[ -s "$output" ]]
}

_pdf_via_pandoc() {
    local input="$1" output="$2"
    deps_has pandoc || return 1
    local -a cmd=(pandoc "$input" -o "$output")
    # Mejor motor tipográfico disponible
    if deps_has lualatex; then
        cmd+=(--pdf-engine=lualatex -V lang=es -V geometry:margin=2.5cm)
    elif deps_has wkhtmltopdf; then
        cmd+=(--pdf-engine=wkhtmltopdf)
    elif deps_has weasyprint; then
        cmd+=(--pdf-engine=weasyprint)
    else
        return 1
    fi
    # shellcheck disable=SC2206
    [[ -n "${DOCFLOW_PANDOC_ARGS:-}" ]] && cmd+=(${DOCFLOW_PANDOC_ARGS})
    "${cmd[@]}" >/dev/null 2>&1 && [[ -s "$output" ]]
}

_pdf_via_wkhtmltopdf() {
    deps_require wkhtmltopdf
    wkhtmltopdf --quiet "$1" "$2" 2>/dev/null && [[ -s "$2" ]]
}

_pdf_via_weasyprint() {
    deps_require weasyprint
    weasyprint "$1" "$2" 2>/dev/null && [[ -s "$2" ]]
}

# _pdf_postprocess <pdf> — PDF/A y/o compresión in situ
_pdf_postprocess() {
    local pdf="$1"
    if [[ "${DOCFLOW_PDF_PDFA:-false}" == "true" ]]; then
        pdf_ops_pdfa "$pdf" "$pdf" || log_warn "No se pudo producir PDF/A: $(basename -- "$pdf")"
    fi
    if [[ "${DOCFLOW_PDF_COMPRESS:-false}" == "true" ]]; then
        pdf_ops_compress "$pdf" "$pdf" || log_warn "No se pudo comprimir: $(basename -- "$pdf")"
    fi
    return 0
}
