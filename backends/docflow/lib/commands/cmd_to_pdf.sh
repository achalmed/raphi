#!/usr/bin/env bash
# lib/commands/cmd_to_pdf.sh — Comando to-pdf: cualquier formato → PDF.

cmd_to_pdf() {
    log_header "Conversión → PDF"
    if [[ $# -eq 0 ]]; then
        log_error "Se requiere al menos una ruta."
        log_plain "  Uso: docflow to-pdf [opciones] <archivo|directorio>..."
        exit "$EXIT_USAGE"
    fi
    dispatch_run pdf "$@"
    exit $?
}

cli_help_to_pdf() {
    cat >&2 <<EOF
${C_BOLD}docflow to-pdf${C_RESET} — Convierte documentos a PDF con el mejor motor disponible.

USO: docflow to-pdf [opciones] <archivo|directorio>...

Formatos: $(registry_exts_for pdf | paste -sd' ')

MOTORES (selección automática por tipo de documento):
  LibreOffice headless   Office/ODF: máxima fidelidad de layout
  pandoc + lualatex      Markdown/LaTeX/HTML: tipografía de alta calidad
  wkhtmltopdf/weasyprint alternativas para HTML

OPCIONES ESPECÍFICAS:
  --pdf-engine <motor>  auto | soffice | pandoc | wkhtmltopdf | weasyprint
  --pdfa                Producir PDF/A-2b (archivado a largo plazo)
  --compress            Comprimir el PDF resultante

EJEMPLOS:
  docflow to-pdf informe.docx
  docflow to-pdf -f pptx,odp -o ~/Escritorio/PDFs ~/Documentos/clases/
  docflow to-pdf --pdfa --compress tesis/
EOF
}
