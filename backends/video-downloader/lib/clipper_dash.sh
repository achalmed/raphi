#!/usr/bin/env bash
# =============================================================================
#  lib/clipper_dash.sh — --clip sobre grabaciones de transmisiones en vivo (DASH)
# =============================================================================
#
#  Por qué existe: Facebook sirve la grabación de un vivo con un manifiesto
#  DASH «dynamic» cuya ventana (timeShiftBufferDepth) es de unos segundos.
#  ffmpeg lo trata como un vivo: no puede saltar a 4:10:30 y se queda
#  esperando sin escribir nada. Pero el manifiesto trae, por representación,
#  una plantilla por número de segmento (FBPredictedMedia, $Number$) con su
#  rango (FBPredictedMediaStartNumber…EndNumber), y cada número existe de
#  verdad en el CDN.
#
#  Método:
#    1. Se baja el manifiesto y se elige la representación de video (la de
#       mayor altura dentro de -q) y la de audio.
#    2. Se calibra: el minuto 0 es el primer segmento (StartNumber); se
#       estima el número del INICIO con FBAverageDuration y se corrige
#       leyendo con ffprobe la marca de tiempo real del segmento.
#    3. Se bajan en paralelo solo los segmentos del tramo (con un margen),
#       se pegan tras su init y el corte exacto lo hace _clip_run_ffmpeg con
#       un -ss por entrada, como en el camino normal.
# =============================================================================

CLIP_DASH_DIR=""     # carpeta temporal de segmentos (se borra al terminar)

# --- clip_dash_applies() ---------------------------------------------------
# Decide si la URL cruda es un manifiesto de vivo con plantilla por número.
# Baja el manifiesto a CLIP_DASH_DIR/manifiesto.mpd (lo reutiliza run).
#
# Arguments:
#   $1 - URL cruda del stream (la que dio yt-dlp -g)
# Returns:
#   0 si aplica este camino; 1 si no (se sigue el camino normal)
clip_dash_applies() {
    local raw="$1"
    [[ "${raw}" == *.mpd* ]] || return 1
    CLIP_DASH_DIR=$(mktemp -d "${TMPDIR:-/tmp}/clip_dash.XXXXXX")
    if ! curl -fsSL --retry 3 -o "${CLIP_DASH_DIR}/manifiesto.mpd" -- "${raw}"; then
        clip_dash_cleanup
        return 1
    fi
    if grep -q 'type="dynamic"' "${CLIP_DASH_DIR}/manifiesto.mpd" \
       && grep -q 'FBPredictedMedia=' "${CLIP_DASH_DIR}/manifiesto.mpd"; then
        return 0
    fi
    clip_dash_cleanup
    return 1
}

# --- clip_dash_cleanup() ---------------------------------------------------
clip_dash_cleanup() {
    [ -n "${CLIP_DASH_DIR}" ] && rm -rf -- "${CLIP_DASH_DIR}"
    CLIP_DASH_DIR=""
    return 0
}

# --- _dash_representations() -----------------------------------------------
# Lista las representaciones del manifiesto, una por línea:
#   tipo|altura|ancho_de_banda|init|plantilla|inicio|fin|duración_media_ms
# con tipo = video|audio; las de texto (subtítulos) se omiten.
_dash_representations() {
    awk '
        function attr(line, name,   m) {
            if (match(line, " " name "=\"[^\"]*\"")) {
                m = substr(line, RSTART + length(name) + 3, RLENGTH - length(name) - 4)
                gsub(/&amp;/, "\\&", m)
                return m
            }
            return ""
        }
        /<Representation/ { inrep = 1; mime = h = bw = ini = pred = s = e = avg = "" }
        inrep {
            line = " " $0
            if ((v = attr(line, "mimeType")) != "")                    mime = v
            if ((v = attr(line, "height")) != "")                      h = v
            if ((v = attr(line, "bandwidth")) != "")                   bw = v
            if ((v = attr(line, "initialization")) != "")              ini = v
            if ((v = attr(line, "FBPredictedMedia")) != "")            pred = v
            if ((v = attr(line, "FBPredictedMediaStartNumber")) != "") s = v
            if ((v = attr(line, "FBPredictedMediaEndNumber")) != "")   e = v
            if ((v = attr(line, "FBAverageDuration")) != "")           avg = v
        }
        /<\/Representation>/ {
            inrep = 0
            tipo = (mime ~ /^video/) ? "video" : (mime ~ /^audio/) ? "audio" : ""
            if (tipo != "" && pred != "" && ini != "")
                print tipo "|" (h == "" ? 0 : h) "|" (bw == "" ? 0 : bw) "|" ini "|" pred "|" s "|" e "|" (avg == "" ? 2000 : avg)
        }
    ' "${CLIP_DASH_DIR}/manifiesto.mpd"
}

# --- _dash_pick() ----------------------------------------------------------
# Elige la representación: audio = la de mayor ancho de banda; video = la de
# mayor altura que no pase OPT_QUALITY (best = sin tope; worst = la menor).
#
# Arguments:
#   $1 - video|audio
# Outputs (stdout):
#   La línea elegida de _dash_representations
_dash_pick() {
    local tipo="$1" tope=999999
    if [ "${tipo}" = "video" ] && [[ "${OPT_QUALITY}" =~ ^[0-9]+$ ]] && [ "${OPT_MODE}" != "best" ]; then
        tope="${OPT_QUALITY}"
    fi
    if [ "${tipo}" = "video" ] && [ "${OPT_QUALITY}" = "worst" ]; then
        _dash_representations | awk -F'|' '$1 == "video"' | sort -t'|' -k2,2n -k3,3n | head -1
        return 0
    fi
    _dash_representations | awk -F'|' -v t="${tipo}" -v tope="${tope}" '$1 == t && $2 <= tope' \
        | sort -t'|' -k2,2n -k3,3n | tail -1
}

# --- _dash_url() -----------------------------------------------------------
# Resuelve una ruta relativa del manifiesto (empieza por ../) contra su URL.
#
# Arguments:
#   $1 - URL del manifiesto; $2 - ruta relativa
_dash_url() {
    local base="${1%%\?*}" rel="$2"
    base="${base%/*}"
    while [[ "${rel}" == ../* ]]; do
        base="${base%/*}"
        rel="${rel#../}"
    done
    printf '%s/%s' "${base}" "${rel}"
}

# --- _dash_fetch_segment() -------------------------------------------------
# Baja un segmento por número. Arguments: $1 plantilla absoluta; $2 número;
# $3 archivo destino.
_dash_fetch_segment() {
    curl -fsS --retry 3 -o "$3" -- "${1//\$Number\$/$2}"
}

# --- _dash_pts_ms() --------------------------------------------------------
# Marca de tiempo (ms) del primer paquete de un segmento, pegado a su init.
# Arguments: $1 init; $2 segmento
_dash_pts_ms() {
    local tmp="${CLIP_DASH_DIR}/sonda.mp4" pts
    cat -- "$1" "$2" > "${tmp}"
    pts=$(ffprobe -v error -show_entries packet=pts_time -of csv=p=0 "${tmp}" 2>/dev/null | head -1) || true
    rm -f -- "${tmp}"
    [ -n "${pts}" ] || return 1
    awk -v p="${pts}" 'BEGIN { printf "%d", p * 1000 }'
}

# --- _dash_calibrate() -----------------------------------------------------
# Encuentra el número de segmento que contiene el INICIO pedido.
#
# Arguments:
#   $1 init local; $2 plantilla absoluta; $3 número inicial; $4 número final;
#   $5 duración media (ms); $6 inicio pedido (s)
# Outputs (stdout):
#   "<número> <pts_cero_ms>"
_dash_calibrate() {
    local init="$1" tpl="$2" first="$3" last="$4" avg="$5" start_s="$6"
    local seg="${CLIP_DASH_DIR}/calibra.m4s" zero pts n target i

    _dash_fetch_segment "${tpl}" "${first}" "${seg}" || return 1
    zero=$(_dash_pts_ms "${init}" "${seg}") || return 1
    target=$(( zero + start_s * 1000 ))
    n=$(( first + start_s * 1000 / avg ))

    # Corrección iterativa: la duración real de cada segmento varía un poco
    for i in 1 2 3 4 5; do
        (( n < first )) && n="${first}"
        (( n > last ))  && n="${last}"
        _dash_fetch_segment "${tpl}" "${n}" "${seg}" || return 1
        pts=$(_dash_pts_ms "${init}" "${seg}") || return 1
        if (( pts > target )); then
            n=$(( n - (pts - target + avg - 1) / avg ))
        elif (( target - pts >= avg )); then
            n=$(( n + (target - pts) / avg ))
        else
            break
        fi
    done
    rm -f -- "${seg}"
    printf '%d %d' "${n}" "${zero}"
}

# --- _dash_assemble() ------------------------------------------------------
# Baja en paralelo los segmentos [desde, hasta] de una representación y los
# pega tras su init. Arguments: $1 línea de representación; $2 URL del
# manifiesto; $3 desde; $4 hasta; $5 archivo de salida.
_dash_assemble() {
    local rep="$1" mpd="$2" from="$3" to="$4" out="$5"
    local ini pred tpl dir
    IFS='|' read -r _ _ _ ini pred _ _ _ <<< "${rep}"
    tpl=$(_dash_url "${mpd}" "${pred}")
    dir="${out}.d"
    mkdir -p -- "${dir}"

    curl -fsS --retry 3 -o "${out}" -- "$(_dash_url "${mpd}" "${ini}")" || return 1
    export -f _dash_fetch_segment
    seq "${from}" "${to}" | xargs -P "${CLIP_DASH_PARALLEL}" -I{} \
        bash -c '_dash_fetch_segment "$1" "$2" "$3/$2.m4s"' _ "${tpl}" {} "${dir}" || return 1

    local n
    for n in $(seq "${from}" "${to}"); do
        [ -s "${dir}/${n}.m4s" ] || { log_error "Falta el segmento ${n}."; return 1; }
        cat -- "${dir}/${n}.m4s" >> "${out}"
    done
    rm -rf -- "${dir}"
}

# --- _dash_offset() --------------------------------------------------------
# Segundos desde el comienzo de un archivo armado hasta el INICIO absoluto.
# Arguments: $1 archivo; $2 inicio absoluto (ms)
_dash_offset() {
    local t0
    t0=$(ffprobe -v error -show_entries format=start_time -of csv=p=0 "$1" 2>/dev/null) || return 1
    awk -v a="$2" -v b="${t0}" 'BEGIN { d = a / 1000 - b; if (d < 0) d = 0; printf "%.3f", d }'
}

# --- clip_dash_prepare() ---------------------------------------------------
# Arma en local los streams del tramo y deja CLIP_VIDEO_URL/CLIP_AUDIO_URL
# apuntando a ellos, con CLIP_SS_VIDEO/CLIP_SS_AUDIO como desplazamiento
# exacto. Después run_clip sigue igual: ffmpeg → verificación.
#
# Arguments:
#   $1 - URL del manifiesto
# Returns:
#   0 si los archivos quedaron listos; 1 en cualquier fallo
clip_dash_prepare() {
    local mpd="$1" vrep="" arep="" ref
    arep=$(_dash_pick audio)
    [ "${OPT_MODE}" != "audio" ] && vrep=$(_dash_pick video)
    ref="${vrep:-${arep}}"
    if [ -z "${ref}" ] || [ -z "${arep}" ]; then
        log_error "El manifiesto no trae representaciones de video y audio utilizables."
        return 1
    fi

    local ini pred first last avg
    IFS='|' read -r _ _ _ ini pred first last avg <<< "${ref}"
    local start_s
    start_s=$(_time_to_seconds "${CLIP_START}")

    log_info "Transmisión en vivo grabada (DASH): calibrando el segmento de ${CLIP_START}..."
    curl -fsS --retry 3 -o "${CLIP_DASH_DIR}/init" -- "$(_dash_url "${mpd}" "${ini}")" || return 1
    local cal n zero
    cal=$(_dash_calibrate "${CLIP_DASH_DIR}/init" "$(_dash_url "${mpd}" "${pred}")" \
                          "${first}" "${last}" "${avg}" "${start_s}") || {
        log_error "No se pudo calibrar la posición del tramo en el manifiesto."
        return 1
    }
    read -r n zero <<< "${cal}"

    # Un segmento de margen antes y dos después: la duración media es aproximada
    local from=$(( n - 1 )) to=$(( n + (CLIP_DURATION * 1000 + avg - 1) / avg + 2 ))
    (( from < first )) && from="${first}"
    (( to > last ))    && to="${last}"
    local abs_ms=$(( zero + start_s * 1000 ))
    log_info "Bajando los segmentos ${from}–${to} ($(( to - from + 1 )) de ~$(( avg / 1000 ))s)..."

    CLIP_VIDEO_URL="" ; CLIP_AUDIO_URL=""
    if [ -n "${vrep}" ]; then
        _dash_assemble "${vrep}" "${mpd}" "${from}" "${to}" "${CLIP_DASH_DIR}/video.mp4" || return 1
        CLIP_VIDEO_URL="${CLIP_DASH_DIR}/video.mp4"
        CLIP_SS_VIDEO=$(_dash_offset "${CLIP_VIDEO_URL}" "${abs_ms}") || return 1
    fi
    _dash_assemble "${arep}" "${mpd}" "${from}" "${to}" "${CLIP_DASH_DIR}/audio.mp4" || return 1
    CLIP_AUDIO_URL="${CLIP_DASH_DIR}/audio.mp4"
    CLIP_SS_AUDIO=$(_dash_offset "${CLIP_AUDIO_URL}" "${abs_ms}") || return 1
    log_debug "Desplazamientos: video ${CLIP_SS_VIDEO:-—}s · audio ${CLIP_SS_AUDIO}s"
    return 0
}
