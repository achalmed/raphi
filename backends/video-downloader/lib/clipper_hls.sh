#!/usr/bin/env bash
# =============================================================================
#  lib/clipper_hls.sh — --clip sobre una transmisión EN VIVO (HLS: YouTube y otros)
# =============================================================================
#
#  Por qué existe: en un directo, yt-dlp no baja secciones («This format cannot
#  be partially downloaded») y ffmpeg no puede saltar dentro de la lista HLS.
#  lib/hls_tramo.py lee la ventana de rebobinado con la hora de cada segmento,
#  baja solo los del tramo (uno tras otro, renovando la lista cuando el servidor
#  responde 403) y los pega en un archivo local; después el corte exacto y la
#  verificación son los de siempre (_clip_run_ffmpeg y _clip_verify).
#
#  Aplica cuando el video está en vivo o cuando el tramo se pidió desde el vivo
#  (-16:30--14:08) o por la hora del reloj (@11:20-@11:22:35).
# =============================================================================

CLIP_HLS_DIR=""     # carpeta temporal del tramo (se borra al terminar)

# --- clip_hls_applies() ----------------------------------------------------
# Arguments:
#   $1 - URL del video
# Returns:
#   0 si hay que ir por este camino; 1 si no
clip_hls_applies() {
    local url="$1"
    [ "${CLIP_KIND}" != "abs" ] && return 0
    local -a access=()
    _clip_access_args access
    local status
    status=$(yt-dlp "${access[@]}" --no-warnings --print "%(live_status)s" -- "${url}" 2>/dev/null | head -1) || true
    [ "${status}" = "is_live" ]
}

# --- clip_hls_cleanup() ----------------------------------------------------
clip_hls_cleanup() {
    [ -n "${CLIP_HLS_DIR}" ] && rm -rf -- "${CLIP_HLS_DIR}"
    CLIP_HLS_DIR=""
    return 0
}

# --- clip_hls_prepare() ----------------------------------------------------
# Baja el tramo a un archivo local y deja listo el corte: CLIP_VIDEO_URL (o
# CLIP_AUDIO_URL en modo audio) apunta a él y CLIP_SS_* al desplazamiento.
#
# Arguments:
#   $1 - URL del video
# Returns:
#   0 si el tramo quedó en disco; 1 si no
clip_hls_prepare() {
    local url="$1"
    local -a access=() extra=()
    _clip_access_args access
    local a
    for a in "${access[@]}"; do extra+=( --yt-dlp-arg="${a}" ); done

    local fsel
    if [ "${OPT_MODE}" = "best" ] || [ "${OPT_QUALITY}" = "best" ]; then
        fsel="b[protocol^=m3u8]"
    elif [ "${OPT_QUALITY}" = "worst" ]; then
        fsel="w[protocol^=m3u8]"
    else
        fsel="b[protocol^=m3u8][height<=?${OPT_QUALITY}]/b[protocol^=m3u8]"
    fi

    CLIP_HLS_DIR=$(mktemp -d "${TMPDIR:-/tmp}/clip_hls.XXXXXX")
    local tramo="${CLIP_HLS_DIR}/tramo.ts" linea
    log_info "Directo: bajando solo los segmentos del tramo ${OPT_CLIP}..."
    linea=$(python3 "${SCRIPT_DIR}/lib/hls_tramo.py" --formato "${fsel}" \
            --inicio "${CLIP_START_RAW}" --fin "${CLIP_END_RAW}" --salida "${tramo}" \
            "${extra[@]}" "${url}" 2> >(_clip_hls_progress)) || {
        log_error "No se pudo bajar el tramo del directo."
        return 1
    }

    local ss dur hora
    ss=$(sed -n 's/.*desplazamiento=\([0-9.]*\).*/\1/p' <<< "${linea}")
    dur=$(sed -n 's/.*duracion=\([0-9.]*\).*/\1/p' <<< "${linea}")
    hora=$(sed -n 's/.*hora=\([0-9:]*\).*/\1/p' <<< "${linea}")
    CLIP_DURATION=$(printf '%.0f' "${dur}")
    if [ "${OPT_MODE}" = "audio" ]; then
        CLIP_AUDIO_URL="${tramo}"; CLIP_SS_AUDIO="${ss}"
    else
        CLIP_VIDEO_URL="${tramo}"; CLIP_AUDIO_URL=""; CLIP_SS_VIDEO="${ss}"
    fi
    if [ -n "${hora}" ] && [ "${CLIP_KIND}" != "reloj" ]; then
        # El nombre lleva la hora real: «-16:30--14:08» deja de tener sentido al rato
        local fin_hora
        fin_hora=$(date -d "${hora} ${CLIP_DURATION} seconds" +%H:%M:%S 2>/dev/null || echo "")
        CLIP_LABEL="${hora//:/.}-${fin_hora//:/.}"
        _clip_compose_output
    fi
    log_ok "Tramo en disco (desde las ${hora:-?}, ${CLIP_DURATION}s)"
    return 0
}

# --- _clip_hls_progress() --------------------------------------------------
# Muestra el avance de hls_tramo.py en una sola línea (y los avisos aparte).
_clip_hls_progress() {
    local l
    while IFS= read -r l; do
        case "${l}" in
            "[tramo] "*segmentos) printf '\r  %s' "${l#\[tramo\] }" >&2 ;;
            *) printf '\n' >&2; log_warn "${l#\[tramo\] }" ;;
        esac
    done
    printf '\n' >&2
}
