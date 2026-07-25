#!/usr/bin/env bash
# =============================================================================
#  lib/downloader.sh — Ejecución de yt-dlp sobre cada objetivo
# =============================================================================
#
#  Reúne los objetivos (URLs posicionales + archivo de lotes) y ejecuta yt-dlp
#  con el array YTDLP_ARGS que arma lib/options.sh. Cada objetivo se procesa de
#  forma independiente: un fallo se registra y se continúa (continue-on-error),
#  y se llevan contadores de éxito/fallo para el resumen final.
# =============================================================================

# ── Contadores globales (los lee lib/summary.sh) ─────────────────────────────
DL_OK_COUNT=0
DL_FAIL_COUNT=0
# Array global de objetivos a procesar
TARGETS=()

# ── collect_targets() ────────────────────────────────────────────────────────
# Rellena TARGETS con las URLs posicionales y, si se dio --batch, con las
# líneas del archivo (ignorando vacías y comentarios que empiezan por #).
#
# Arguments:
#   $1 - Nombre (nameref) del array de URLs posicionales (OPT_URLS)
#   $2 - Ruta del archivo de lotes (puede ir vacía)
collect_targets() {
    local -n urls_ref="$1"
    local batch_file="$2"
    TARGETS=()

    local url
    for url in "${urls_ref[@]}"; do
        TARGETS+=("${url}")
    done

    [ -z "${batch_file}" ] && return 0
    if [ ! -f "${batch_file}" ]; then
        log_error "Archivo de lotes no encontrado: ${batch_file}"
        exit 3
    fi

    local line
    while IFS= read -r line || [ -n "${line}" ]; do
        line="${line#"${line%%[![:space:]]*}"}"   # recorta espacios iniciales
        [ -z "${line}" ] && continue               # ignora líneas vacías
        [[ "${line}" == \#* ]] && continue         # ignora comentarios
        TARGETS+=("${line}")
    done < "${batch_file}"
}

# ── run_download() ───────────────────────────────────────────────────────────
# Descarga un objetivo con el array YTDLP_ARGS ya construido.
# El `--` separa las opciones de la URL (protege URLs que empiezan por -).
#
# Arguments:
#   $1 - URL/objetivo
# Returns:
#   El código de salida de yt-dlp (0 = éxito)
run_download() {
    local url="$1"
    local rc=0
    # `|| rc=$?` evita que set -e aborte: queremos seguir con el siguiente objetivo
    yt-dlp "${YTDLP_ARGS[@]}" -- "${url}" || rc=$?
    return "${rc}"
}

# ── run_info() ───────────────────────────────────────────────────────────────
# Imprime metadatos del objetivo sin descargar. Usa jq para un resumen legible
# si está disponible; si no, vuelca el JSON crudo de yt-dlp.
#
# Arguments:
#   $1 - URL/objetivo
run_info() {
    local url="$1"
    local rc=0
    if command -v jq &>/dev/null; then
        yt-dlp "${YTDLP_ARGS[@]}" --skip-download --dump-json -- "${url}" \
            | jq '{titulo: .title, autor: .uploader, duracion: .duration_string,
                   vistas: .view_count, fecha: .upload_date, resolucion: .resolution,
                   formato: .ext, url: .webpage_url}' || rc=$?
    else
        yt-dlp "${YTDLP_ARGS[@]}" --skip-download --dump-json -- "${url}" || rc=$?
    fi
    return "${rc}"
}

# ── run_list_formats() ───────────────────────────────────────────────────────
# Lista todos los formatos disponibles del objetivo (sin descargar).
#
# Arguments:
#   $1 - URL/objetivo
run_list_formats() {
    local url="$1"
    local rc=0
    yt-dlp -F "${YTDLP_ARGS[@]}" -- "${url}" || rc=$?
    return "${rc}"
}

# ── dispatch_target() ────────────────────────────────────────────────────────
# Elige la acción según el modo y actualiza los contadores de éxito/fallo.
#
# Arguments:
#   $1 - Modo (video|audio|best|subs|info|formats)
#   $2 - URL/objetivo
#   $3 - Índice actual (para el encabezado)
#   $4 - Total de objetivos
dispatch_target() {
    local mode="$1" url="$2" idx="$3" total="$4"
    echo ""
    log_title "[${idx}/${total}] ${url}"
    log_separator "─" 70

    local rc=0
    case "${mode}" in
        info)    run_info "${url}" || rc=$? ;;
        formats) run_list_formats "${url}" || rc=$? ;;
        *)
            # Con --clip activo se usa la ruta robusta de lib/clipper.sh en vez
            # del descargador de secciones de yt-dlp (que trunca en DASH)
            if [ -n "${OPT_CLIP}" ]; then
                run_clip "${url}" || rc=$?
            else
                run_download "${url}" || rc=$?
            fi ;;
    esac

    # yt-dlp usa 101 al alcanzar --max-downloads: es una parada esperada, no un fallo
    # No usar ((var++)): con valor 0 devuelve estado 1 y set -e abortaría el script
    if [ "${rc}" -eq 0 ] || [ "${rc}" -eq 101 ]; then
        log_ok "Completado: ${url}"
        DL_OK_COUNT=$((DL_OK_COUNT + 1))
    else
        log_error "Falló (código ${rc}): ${url}"
        DL_FAIL_COUNT=$((DL_FAIL_COUNT + 1))
    fi
}

# ── run_all_targets() ────────────────────────────────────────────────────────
# Recorre TARGETS y procesa cada uno; aplica la espera entre videos si se pidió.
#
# Arguments:
#   $1 - Modo activo
#   $2 - Segundos de espera entre objetivos (0 = sin espera)
run_all_targets() {
    local mode="$1" sleep_secs="$2"
    local total="${#TARGETS[@]}"
    local i=0

    local url
    for url in "${TARGETS[@]}"; do
        i=$((i + 1))
        dispatch_target "${mode}" "${url}" "${i}" "${total}"
        # Pausa de cortesía entre objetivos (no tras el último)
        if [ "${sleep_secs}" != "0" ] && [ "${i}" -lt "${total}" ]; then
            log_debug "Esperando ${sleep_secs}s antes del siguiente objetivo..."
            sleep "${sleep_secs}"
        fi
    done
}
