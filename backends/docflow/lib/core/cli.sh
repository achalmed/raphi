#!/usr/bin/env bash
# lib/core/cli.sh — Parsing de argumentos y ayuda.
# Un solo lugar para todos los flags: añadir una opción = tocar este archivo
# (y defaults.conf si tiene valor por defecto configurable).
# shellcheck disable=SC2034  # las variables DOCFLOW_* que deja el parser las leen los comandos y los workers

# cli_parse_global "$@" — deja DOCFLOW_COMMAND y DOCFLOW_ARGS (posicionales)
cli_parse_global() {
    DOCFLOW_COMMAND="${1:-}"
    [[ $# -gt 0 ]] && shift
    declare -ga DOCFLOW_ARGS=()

    case "$DOCFLOW_COMMAND" in
        -h|--help) DOCFLOW_COMMAND="help"; return 0 ;;
        --version) DOCFLOW_COMMAND="version"; return 0 ;;
        # Estos comandos parsean sus propios argumentos (operaciones con
        # flags propios) o los reciben ya resueltos del proceso padre:
        pdf|__worker) DOCFLOW_ARGS=("$@"); return 0 ;;
    esac

    DOCFLOW_EXCLUDES="${DOCFLOW_DEFAULT_EXCLUDES}"
    DOCFLOW_EXCLUDE_REGEX=""
    DOCFLOW_INCLUDE_GLOB=""
    DOCFLOW_FORMATS_FILTER=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            # --- Entrada / salida ------------------------------------------
            -i|--input)         DOCFLOW_ARGS+=("$2"); shift 2 ;;
            -o|--output|--output-dir) DOCFLOW_OUTPUT_DIR="$2"; shift 2 ;;
            -f|--formats)       DOCFLOW_FORMATS_FILTER="$2"; shift 2 ;;
            --include)          DOCFLOW_INCLUDE_GLOB="$2"; shift 2 ;;
            -e|--exclude)       DOCFLOW_EXCLUDES+=" $2"; shift 2 ;;
            --exclude-regex)    DOCFLOW_EXCLUDE_REGEX="$2"; shift 2 ;;
            --no-default-excludes) DOCFLOW_EXCLUDES=""; shift ;;
            # --- Comportamiento --------------------------------------------
            -w|--overwrite)     DOCFLOW_OVERWRITE=true; shift ;;
            -n|--dry-run)       DOCFLOW_DRY_RUN=true; shift ;;
            --resume)           DOCFLOW_RESUME=true; shift ;;   # alias semántico:
                                # la salida existente y válida se omite (defecto)
            -j|--jobs)          DOCFLOW_JOBS="$2"; shift 2 ;;
            --no-cache)         DOCFLOW_CACHE=false; shift ;;
            --no-verify)        DOCFLOW_VERIFY=false; shift ;;
            --force)            DOCFLOW_FORCE=true; shift ;;
            # --- Originales -------------------------------------------------
            --delete)           DOCFLOW_DELETE_ORIGINALS=true; shift ;;
            --backup)           DOCFLOW_BACKUP_ORIGINALS=true; shift ;;
            # --- Logging -----------------------------------------------------
            -v|--verbose)       logger_set_level debug; shift ;;
            --trace)            logger_set_level trace; shift ;;
            -q|--quiet)         logger_set_level quiet; shift ;;
            --json)             DOCFLOW_JSON=true; logger_set_level warn; shift ;;
            -l|--log)           logger_set_file "$2"; shift 2 ;;
            --log-level)        logger_set_level "$2" || { log_error "Nivel inválido: $2"; exit "$EXIT_USAGE"; }; shift 2 ;;
            # --- Markdown Engine --------------------------------------------
            --flavor)           DOCFLOW_MD_FLAVOR="$2"; shift 2 ;;
            --no-metadata)      DOCFLOW_MD_METADATA=false; shift ;;
            --no-clean)         DOCFLOW_MD_CLEAN=false; shift ;;
            --no-notes)         DOCFLOW_MD_INCLUDE_NOTES=false; shift ;;
            --slide-separator)  DOCFLOW_MD_SLIDE_SEPARATOR="$2"; shift 2 ;;
            --pandoc-args)      DOCFLOW_PANDOC_ARGS="$2"; shift 2 ;;
            # --- Media Engine -----------------------------------------------
            --img-format)       DOCFLOW_IMG_FORMAT="$2"; shift 2 ;;
            --img-quality)      DOCFLOW_IMG_QUALITY="$2"; shift 2 ;;
            --img-max-width)    DOCFLOW_IMG_MAX_WIDTH="$2"; shift 2 ;;
            --img-optimize)     DOCFLOW_IMG_OPTIMIZE=true; shift ;;
            # --- PDF Engine --------------------------------------------------
            --pdf-engine)       DOCFLOW_PDF_ENGINE="$2"; shift 2 ;;
            --pdfa)             DOCFLOW_PDF_PDFA=true; shift ;;
            --compress)         DOCFLOW_PDF_COMPRESS=true; shift ;;
            # --- OCR ----------------------------------------------------------
            --ocr)              DOCFLOW_OCR=true; shift ;;
            --ocr-lang)         DOCFLOW_OCR_LANG="$2"; shift 2 ;;
            # --- Watch --------------------------------------------------------
            --interval)         DOCFLOW_WATCH_INTERVAL="$2"; shift 2 ;;
            # --- Reportes -----------------------------------------------------
            --report)           DOCFLOW_REPORT_FORMATS="$2"; shift 2 ;;
            --report-out)       DOCFLOW_REPORT_OUT="$2"; shift 2 ;;
            # --- Hooks --------------------------------------------------------
            --pre-hook)         DOCFLOW_PRE_HOOK="$2"; shift 2 ;;
            --post-hook)        DOCFLOW_POST_HOOK="$2"; shift 2 ;;
            # --- Config -------------------------------------------------------
            --config)           DOCFLOW_CONFIG_FILE="$2"; config_load_toml "$2"; shift 2 ;;
            # --- Genéricos ----------------------------------------------------
            -h|--help)          cli_show_command_help "$DOCFLOW_COMMAND"; exit 0 ;;
            --)                 shift; DOCFLOW_ARGS+=("$@"); break ;;
            -*)
                log_error "Flag desconocido: $1"
                log_plain "  Ejecuta 'docflow ${DOCFLOW_COMMAND} --help' para ver las opciones."
                exit "$EXIT_USAGE" ;;
            *)                  DOCFLOW_ARGS+=("$1"); shift ;;
        esac
    done

    # --resume implica no sobreescribir salidas existentes
    [[ "${DOCFLOW_RESUME}" == "true" ]] && DOCFLOW_OVERWRITE=false

    # --backup tiene precedencia sobre --delete (nunca ambos)
    [[ "${DOCFLOW_BACKUP_ORIGINALS}" == "true" ]] && DOCFLOW_DELETE_ORIGINALS=false
    return 0
}

cli_show_help() {
    cat >&2 <<EOF

${C_BOLD}${DOCFLOW_NAME} v${DOCFLOW_VERSION}${C_RESET} — Suite profesional de conversión documental
${C_BOLD}Autor:${C_RESET} ${DOCFLOW_AUTHOR} · ${DOCFLOW_URL}

${C_BOLD}USO:${C_RESET}
  docflow <COMANDO> [OPCIONES] <RUTA...>

${C_BOLD}COMANDOS DE CONVERSIÓN:${C_RESET}
  ${C_GREEN}to-md${C_RESET}       Office/ODF/PDF → Markdown (imágenes, notas, tablas, metadatos)
  ${C_GREEN}to-pdf${C_RESET}      Office/ODF/Markdown/HTML/LaTeX → PDF (mejor motor disponible)
  ${C_GREEN}to-odf${C_RESET}      MS Office → OpenDocument (docx→odt, pptx→odp, xlsx→ods, plantillas)
  ${C_GREEN}to-office${C_RESET}   OpenDocument → MS Office (odt→docx, odp→pptx, ods→xlsx)

${C_BOLD}OPERACIONES PDF:${C_RESET}
  ${C_GREEN}pdf${C_RESET}         merge | split | rotate | extract | compress | pdfa | encrypt |
              decrypt | watermark | ocr | info   (docflow pdf --help)

${C_BOLD}UTILIDADES:${C_RESET}
  ${C_GREEN}watch${C_RESET}       Vigilar directorio y convertir automáticamente (inotify/polling)
  ${C_GREEN}report${C_RESET}      Reporte de la última sesión (html, csv, json, md)
  ${C_GREEN}index${C_RESET}       Índice global + árbol de documentos convertidos
  ${C_GREEN}doctor${C_RESET}      Diagnóstico de dependencias con instrucciones de instalación
  ${C_GREEN}formats${C_RESET}     Tabla de formatos soportados y sus capacidades
  ${C_GREEN}cache${C_RESET}       Gestión del caché (stats | clear | prune)
  ${C_GREEN}config${C_RESET}      Configuración de usuario (init | show | path)

${C_BOLD}OPCIONES GLOBALES (resumen):${C_RESET}
  -o, --output-dir <dir>   Directorio de salida (defecto: junto al original)
  -f, --formats <lista>    Solo estas extensiones: docx,odt,pptx
  -e, --exclude <patrón>   Excluir directorio/patrón (repetible)
      --exclude-regex <re> Excluir rutas por expresión regular
      --include <glob>     Incluir solo archivos que casen con el glob
  -j, --jobs <n>           Workers en paralelo (defecto: nproc)
  -w, --overwrite          Sobreescribir salidas existentes
  -n, --dry-run            Simular sin escribir nada
      --resume             Reanudar lote interrumpido (omite salidas válidas)
      --no-cache           Ignorar el caché de conversiones
      --backup / --delete  Mover a _backup/ o eliminar SOLO originales exitosos
      --force              No pedir confirmaciones (automatización)
  -v, --verbose  -q, --quiet  --json  -l, --log <archivo>
      --report <fmts>      Generar reporte al terminar: html,csv,json,md
      --pre-hook / --post-hook <cmd>   Comandos alrededor de cada conversión

  Ayuda por comando: ${C_CYAN}docflow <comando> --help${C_RESET}
  Configuración:     ${C_CYAN}~/.config/docflow/config.toml${C_RESET} (docflow config init)

${C_BOLD}EJEMPLOS:${C_RESET}
  docflow to-md tesis/                        # carpeta completa a Markdown
  docflow to-md --flavor obsidian --img-format webp ~/Documentos/apuntes/
  docflow to-pdf -f docx,pptx --report html ~/Documentos/trabajos/
  docflow to-odf --backup ~/Documentos/legacy/
  docflow pdf merge unido.pdf cap1.pdf cap2.pdf
  docflow watch ~/Descargas --formats docx --post-hook 'notify-send docflow "\$DOCFLOW_OUTPUT"'

EOF
}

# cli_show_command_help <comando> — ayuda breve contextual
cli_show_command_help() {
    local fn="cli_help_${1//-/_}"
    if declare -F "$fn" >/dev/null; then "$fn"; else cli_show_help; fi
}
