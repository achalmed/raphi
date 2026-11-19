#!/usr/bin/env bash
# =============================================================================
#  lib/clipper.sh — Recorte exacto de tramos (--clip INICIO-FIN)
# =============================================================================
#
#  Por qué existe: el descargador de secciones de yt-dlp (--download-sections)
#  puede truncar el stream de video en sitios DASH (Facebook sirve video y
#  audio por separado), dejando clips con imagen congelada y audio completo.
#
#  Método robusto usado aquí:
#    1. yt-dlp -g extrae las URLs crudas del CDN (sin descargar)
#    2. ffmpeg busca por rangos HTTP hasta el INICIO (-ss de entrada),
#       decodifica desde el keyframe previo y re-codifica el tramo completo
#       → cada frame es decodificable y la sincronía A/V es exacta
#    3. El resultado se VERIFICA con ffprobe (duración por stream): un clip
#       truncado se reporta como fallo, nunca se entrega en silencio
# =============================================================================

# --- Estado global del clip (lo fija clip_parse_range desde main) ----------
CLIP_START=""        # tiempo de inicio (sin «-» ni «@») para el corte normal
CLIP_START_RAW=""    # extremos tal como los escribió el usuario
CLIP_END_RAW=""
CLIP_KIND="abs"      # abs (desde el comienzo) · vivo (hacia atrás desde el vivo) · reloj (hora)
CLIP_BASE=""         # «<título> [<id>]» saneado
CLIP_DURATION=0      # duración del tramo en segundos
CLIP_LABEL=""        # etiqueta para el nombre de archivo (sin ':')
CLIP_OUTPUT=""       # ruta final del clip (la fija _clip_output_path)
CLIP_VIDEO_URL=""    # URL cruda del stream de video
CLIP_AUDIO_URL=""    # URL cruda del stream de audio ("" si es combinado)
CLIP_SS_VIDEO=""     # -ss propio del video ("" = CLIP_START); lo fija clipper_dash.sh
CLIP_SS_AUDIO=""     # -ss propio del audio ("" = CLIP_START); lo fija clipper_dash.sh

# --- _time_to_seconds() ----------------------------------------------------
# Convierte H:MM:SS, MM:SS o SS a segundos totales.
# El prefijo 10# evita que "08"/"09" se interpreten como octal inválido.
#
# Arguments:
#   $1 - Tiempo en formato H:MM:SS, MM:SS o SS
# Outputs (stdout):
#   Segundos totales como entero
_time_to_seconds() {
    local p1 p2 p3
    IFS=: read -r p1 p2 p3 <<< "$1"
    if [ -n "${p3:-}" ]; then
        echo $(( 10#${p1} * 3600 + 10#${p2} * 60 + 10#${p3} ))
    elif [ -n "${p2:-}" ]; then
        echo $(( 10#${p1} * 60 + 10#${p2} ))
    else
        echo $(( 10#${p1} ))
    fi
}

# --- clip_parse_range() ----------------------------------------------------
# Valida y descompone el rango INICIO-FIN de --clip. Se llama desde main
# en la fase de validación, una sola vez.
#
# Arguments:
#   $1 - Rango, ej. "2:46:00-2:47:00", "90-150", "1:30-2:00"
# Returns:
#   0 y fija CLIP_START/CLIP_DURATION/CLIP_LABEL; exit 2 si es inválido
clip_parse_range() {
    local range="$1"
    # Un extremo: H:MM:SS, MM:SS o SS (con decimales); «-» delante = hacia atrás
    # desde el vivo; «@» delante = hora del reloj. Separador: «-», «..» o « a ».
    local t='[0-9]+(:[0-9]{1,2}){0,2}([.][0-9]+)?'
    local e="(@${t}|-?${t})"
    if [[ ! "${range}" =~ ^[[:space:]]*${e}[[:space:]]*(-|[.][.]|[[:space:]]a[[:space:]])[[:space:]]*${e}[[:space:]]*$ ]]; then
        log_error "Tramo no válido: '${range}'. Ejemplos: 2:46:00-2:47:00 · -16:30--14:08 (desde el vivo) · @11:20-@11:22:35 (por la hora)"
        exit 2
    fi
    # BASH_REMATCH: 1 = primer extremo (2–5, sus grupos internos); 6 = separador; 7 = segundo extremo
    local start_raw="${BASH_REMATCH[1]}" end_raw="${BASH_REMATCH[7]}"

    local k1=abs k2=abs
    [[ "${start_raw}" == -* ]] && k1=vivo; [[ "${start_raw}" == @* ]] && k1=reloj
    [[ "${end_raw}" == -* ]] && k2=vivo;   [[ "${end_raw}" == @* ]] && k2=reloj
    if [ "${k1}" != "${k2}" ]; then
        log_error "Los dos extremos del tramo deben ser de la misma clase: '${range}'"
        exit 2
    fi

    local s="${start_raw#[-@]}" f="${end_raw#[-@]}" start_secs end_secs
    if [ "${k1}" = reloj ]; then   # en la hora, «11:20» es HH:MM, no MM:SS
        [[ "${s%%.*}" =~ ^[0-9]+:[0-9]+$ ]] && s="${s}:00"
        [[ "${f%%.*}" =~ ^[0-9]+:[0-9]+$ ]] && f="${f}:00"
    fi
    start_secs=$(_time_to_seconds "${s%%.*}")
    end_secs=$(_time_to_seconds "${f%%.*}")
    case "${k1}" in
        vivo)  local tmp="${start_secs}"; start_secs="${end_secs}"; end_secs="${tmp}" ;;  # -16:30 va antes que -14:08
        reloj) [ "${end_secs}" -le "${start_secs}" ] && end_secs=$(( end_secs + 86400 )) ;;
    esac
    if [ "${end_secs}" -le "${start_secs}" ]; then
        log_error "El FIN del tramo (${end_raw}) debe ser posterior al INICIO (${start_raw})"
        exit 2
    fi

    CLIP_KIND="${k1}"
    CLIP_START_RAW="${start_raw}"
    CLIP_END_RAW="${end_raw}"
    CLIP_START="${s}"
    CLIP_DURATION=$(( end_secs - start_secs ))
    # ':' es inválido en FAT/NTFS; se usa '.' en el nombre de archivo
    CLIP_LABEL="${start_raw//:/.}_${end_raw//:/.}"
    [ "${k1}" != vivo ] && CLIP_LABEL="${s//:/.}-${f//:/.}"
    log_debug "Clip: clase=${CLIP_KIND} inicio=${CLIP_START_RAW} duración=${CLIP_DURATION}s"
    return 0
}

# --- clip_looks_like_range() -----------------------------------------------
# ¿Es este argumento suelto un tramo? (para «main.sh <url> 1:20-2:30»)
clip_looks_like_range() {
    local t='[0-9]+(:[0-9]{1,2}){0,2}([.][0-9]+)?'
    local e="(@${t}|-?${t})"
    [[ "$1" =~ ^${e}(-|[.][.])${e}$ ]] && [[ "$1" == *[:@.]* || "$1" =~ ^[0-9]+-[0-9]+$ ]]
}

# --- _clip_access_args() ---------------------------------------------------
# Rellena el array (nameref) con las opciones de acceso que necesitan las
# llamadas de extracción de yt-dlp (cookies, proxy, user-agent).
#
# Arguments:
#   $1 - Nombre del array a rellenar
_clip_access_args() {
    local -n args_ref="$1"
    args_ref=( --no-playlist )   # --clip opera sobre UN video, nunca una playlist
    [ -n "${OPT_COOKIES_FILE}" ]    && args_ref+=( --cookies "${OPT_COOKIES_FILE}" )
    [ -n "${OPT_COOKIES_BROWSER}" ] && args_ref+=( --cookies-from-browser "${OPT_COOKIES_BROWSER}" )
    [ -n "${OPT_PROXY}" ]           && args_ref+=( --proxy "${OPT_PROXY}" )
    [ -n "${OPT_USER_AGENT}" ]      && args_ref+=( --user-agent "${OPT_USER_AGENT}" )
    return 0   # el último test puede ser falso; sin esto set -e abortaría
}

# --- _clip_extract_urls() --------------------------------------------------
# Extrae las URLs crudas de los streams con yt-dlp -g, respetando la calidad
# elegida. Si el sitio no ofrece streams separados, cae al formato combinado.
#
# Arguments:
#   $1 - URL del video
# Returns:
#   0 y fija CLIP_VIDEO_URL/CLIP_AUDIO_URL; 1 si no se pudo extraer nada
_clip_extract_urls() {
    local url="$1"
    local -a access=()
    _clip_access_args access

    # Selector de video según la calidad pedida (mismo criterio que options.sh)
    local vsel
    if [ "${OPT_MODE}" = "best" ] || [ "${OPT_QUALITY}" = "best" ]; then
        vsel="bv*"
    elif [ "${OPT_QUALITY}" = "worst" ]; then
        vsel="wv*"
    else
        vsel="bv*"
        access+=( -S "res:${OPT_QUALITY}" )   # el lado corto, como en options.sh
    fi

    CLIP_VIDEO_URL="" ; CLIP_AUDIO_URL=""
    # En modo audio solo hace falta el stream de audio
    if [ "${OPT_MODE}" != "audio" ]; then
        CLIP_VIDEO_URL=$(yt-dlp "${access[@]}" -g -f "${vsel}" -- "${url}" 2>/dev/null | head -1) || true
    fi
    CLIP_AUDIO_URL=$(yt-dlp "${access[@]}" -g -f "ba" -- "${url}" 2>/dev/null | head -1) || true

    # Fallback: formato combinado (sitios sin streams separados)
    if { [ "${OPT_MODE}" != "audio" ] && [ -z "${CLIP_VIDEO_URL}" ]; } \
       || { [ "${OPT_MODE}" = "audio" ] && [ -z "${CLIP_AUDIO_URL}" ]; }; then
        local combined
        combined=$(yt-dlp "${access[@]}" -g -f "b" -- "${url}" 2>/dev/null | head -1) || true
        if [ -z "${combined}" ]; then
            log_error "No se pudieron extraer las URLs de los streams (¿requiere cookies?)."
            return 1
        fi
        CLIP_VIDEO_URL="${combined}" ; CLIP_AUDIO_URL=""
    fi
    log_debug "Stream video: ${CLIP_VIDEO_URL:0:60}..."
    return 0
}

# --- _clip_sanitize_base() -------------------------------------------------
# Blinda el nombre base contra títulos vacíos o inservibles. Facebook y otros
# sitios a veces devuelven un título vacío o compuesto solo de puntos/espacios;
# con la plantilla "<título> [<id>]" eso produce ". [id]…" o " [id]…", es decir
# un archivo OCULTO (empieza por '.') o con espacio inicial. Recorta esos
# caracteres del arranque y, si tras el recorte no queda nada imprimible, cae al
# prefijo de respaldo con marca de tiempo (CLIP_FALLBACK_PREFIX en config.sh).
#
# Arguments:
#   $1 - Nombre base candidato ("<título> [<id>]")
# Outputs (stdout):
#   Nombre base saneado: nunca vacío, nunca empieza por '.' ni por espacio
_clip_sanitize_base() {
    local base="$1"
    # Recorta el prefijo de puntos/espacios: ${base%%[! .]*} aísla justo ese
    # tramo inicial (todo hasta el primer carácter que no es '.' ni ' ') y el
    # ${base#…} lo elimina. Un título normal no tiene ese prefijo y queda igual.
    base="${base#"${base%%[! .]*}"}"
    if [ -z "${base}" ]; then
        base="${CLIP_FALLBACK_PREFIX}_$(date +%Y%m%d_%H%M%S)"
    fi
    printf '%s' "${base}"
}

# --- _clip_output_path() ---------------------------------------------------
# Calcula la ruta final del clip: "<título> [<id>] (clip <rango>).<ext>".
#
# Arguments:
#   $1 - URL del video
_clip_output_path() {
    local url="$1"
    local -a access=()
    _clip_access_args access

    local base
    base=$(yt-dlp "${access[@]}" "${TITLE_CLEANUP_ARGS[@]}" --print "%(title)s [%(id)s]" -- "${url}" 2>/dev/null \
           | head -1) || true
    base="${base//\//_}"                    # '/' en el título rompería la ruta
    CLIP_BASE=$(_clip_sanitize_base "${base}")   # nunca vacío, nunca dotfile oculto
    _clip_compose_output
}

# --- _clip_compose_output() ------------------------------------------------
# Arma CLIP_OUTPUT con CLIP_BASE y CLIP_LABEL (clipper_hls.sh la vuelve a
# llamar cuando el tramo de un directo se rotula con su hora real).
_clip_compose_output() {
    local ext="${OPT_CONTAINER}"
    [ "${OPT_MODE}" = "audio" ] && ext="${OPT_AUDIO_FORMAT}"
    CLIP_OUTPUT="${OPT_OUTPUT_DIR}/${CLIP_BASE} (clip ${CLIP_LABEL}).${ext}"
}

# --- _clip_audio_codec_args() ----------------------------------------------
# Traduce OPT_AUDIO_FORMAT al codificador ffmpeg correspondiente (modo audio).
#
# Arguments:
#   $1 - Nombre del array a rellenar
_clip_audio_codec_args() {
    local -n args_ref="$1"
    case "${OPT_AUDIO_FORMAT}" in
        mp3)  args_ref=( -c:a libmp3lame -q:a 2 ) ;;
        m4a|aac) args_ref=( -c:a aac -b:a "${CLIP_AUDIO_BITRATE}" ) ;;
        opus) args_ref=( -c:a libopus ) ;;
        flac) args_ref=( -c:a flac ) ;;
        wav)  args_ref=( -c:a pcm_s16le ) ;;
        *)    args_ref=( -c:a aac -b:a "${CLIP_AUDIO_BITRATE}" ) ;;
    esac
}

# --- _clip_run_ffmpeg() ----------------------------------------------------
# Construye y ejecuta el comando ffmpeg. El -ss va ANTES de cada -i (búsqueda
# de entrada): ffmpeg salta por rangos HTTP hasta el keyframe previo, decodifica
# y descarta hasta el punto exacto — por eso el corte es preciso al frame.
#
# Returns:
#   El código de salida de ffmpeg
_clip_run_ffmpeg() {
    local -a cmd=( ffmpeg -hide_banner -y )
    local ssv="${CLIP_SS_VIDEO:-${CLIP_START}}" ssa="${CLIP_SS_AUDIO:-${CLIP_START}}"
    if [ "${LOGGER_VERBOSE}" = true ]; then
        cmd+=( -loglevel info -stats )
    else
        cmd+=( -loglevel error -nostats )
    fi

    if [ "${OPT_MODE}" = "audio" ]; then
        local -a acodec=()
        _clip_audio_codec_args acodec
        cmd+=( -ss "${ssa}" -t "${CLIP_DURATION}" -i "${CLIP_AUDIO_URL}" -vn "${acodec[@]}" )
    elif [ -n "${CLIP_AUDIO_URL}" ]; then
        # Streams separados (DASH): un -ss por cada entrada
        cmd+=( -ss "${ssv}" -t "${CLIP_DURATION}" -i "${CLIP_VIDEO_URL}" )
        cmd+=( -ss "${ssa}" -t "${CLIP_DURATION}" -i "${CLIP_AUDIO_URL}" )
        cmd+=( -map 0:v:0 -map 1:a:0 )
        cmd+=( -c:v libx264 -crf "${CLIP_VIDEO_CRF}" -preset "${CLIP_VIDEO_PRESET}" )
        cmd+=( -c:a aac -b:a "${CLIP_AUDIO_BITRATE}" -movflags +faststart -shortest )
    else
        # Formato combinado: una sola entrada ('?' = audio opcional). Con el tramo de un directo ya en disco
        # (CLIP_SEEK_SALIDA, lib/clipper_hls.sh) el -ss va DESPUÉS de -i: buscar antes deja el video unos segundos
        # tarde respecto del audio en esos MPEG-TS pegados (se vio el 2026-11-19: video desde 2,1 s)
        if [ "${CLIP_SEEK_SALIDA:-false}" = true ]; then
            cmd+=( -i "${CLIP_VIDEO_URL}" -ss "${ssv}" -t "${CLIP_DURATION}" )
        else
            cmd+=( -ss "${ssv}" -t "${CLIP_DURATION}" -i "${CLIP_VIDEO_URL}" )
        fi
        cmd+=( -map 0:v:0 -map "0:a:0?" )
        cmd+=( -c:v libx264 -crf "${CLIP_VIDEO_CRF}" -preset "${CLIP_VIDEO_PRESET}" )
        cmd+=( -c:a aac -b:a "${CLIP_AUDIO_BITRATE}" -movflags +faststart -shortest )
    fi

    cmd+=( "${CLIP_OUTPUT}" )
    "${cmd[@]}"
}

# --- _clip_verify() --------------------------------------------------------
# La red de seguridad: comprueba con ffprobe que cada stream del clip dure lo
# pedido (tolerancia 1.5s). Detecta exactamente el fallo de video congelado
# que motivó este módulo, en vez de entregar un archivo defectuoso.
#
# Returns:
#   0 si el clip está completo; 1 si algún stream quedó truncado
_clip_verify() {
    local dv="" da=""
    if [ "${OPT_MODE}" != "audio" ]; then
        dv=$(ffprobe -v error -select_streams v:0 -show_entries stream=duration \
             -of csv=p=0 "${CLIP_OUTPUT}" 2>/dev/null) || true
    fi
    da=$(ffprobe -v error -select_streams a:0 -show_entries stream=duration \
         -of csv=p=0 "${CLIP_OUTPUT}" 2>/dev/null) || true

    local problems
    problems=$(awk -v dv="${dv:-0}" -v da="${da:-0}" -v want="${CLIP_DURATION}" \
                   -v video_mode="$([ "${OPT_MODE}" != "audio" ] && echo 1 || echo 0)" \
        'BEGIN {
            n = 0
            if (video_mode && dv < want - 1.5) { printf "video %.1fs/%ds ", dv, want; n++ }
            if (da < want - 1.5)               { printf "audio %.1fs/%ds ", da, want; n++ }
            exit n
        }') || true

    if [ -n "${problems}" ]; then
        log_error "Clip truncado (${problems}) — el archivo se conserva para inspección."
        return 1
    fi
    log_ok "Verificado con ffprobe: video ${dv:-—}s · audio ${da:-—}s (esperado ${CLIP_DURATION}s)"
    return 0
}

# --- run_clip() ------------------------------------------------------------
# Orquesta el recorte de un objetivo: extraer URLs → ruta → ffmpeg → verificar.
# La llama dispatch_target (lib/downloader.sh) cuando OPT_CLIP está activo.
#
# Arguments:
#   $1 - URL del video
# Returns:
#   0 si el clip se creó y verificó; 1 en cualquier fallo
run_clip() {
    local url="$1"
    CLIP_SS_VIDEO="" ; CLIP_SS_AUDIO=""
    local en_vivo=false
    clip_hls_applies "${url}" && en_vivo=true
    if [ "${en_vivo}" = false ]; then
        _clip_extract_urls "${url}" || return 1
    fi
    _clip_output_path "${url}"

    if [ "${OPT_SIMULATE}" = true ]; then
        log_info "[SIMULACIÓN] Se recortaría ${OPT_CLIP}$([ "${en_vivo}" = true ] && echo ' del directo') → ${CLIP_OUTPUT}"
        return 0
    fi

    # Transmisión en vivo (HLS): se bajan solo los segmentos del tramo (lib/clipper_hls.sh)
    if [ "${en_vivo}" = true ]; then
        if ! clip_hls_prepare "${url}"; then
            clip_hls_cleanup
            return 1
        fi
    fi

    # Grabación de un vivo (manifiesto DASH «dynamic»): ffmpeg no puede saltar
    # dentro de él; se bajan solo los segmentos del tramo (lib/clipper_dash.sh)
    local raw="${CLIP_VIDEO_URL:-${CLIP_AUDIO_URL}}"
    [ "${OPT_MODE}" = "audio" ] && raw="${CLIP_AUDIO_URL}"
    if [ "${en_vivo}" = false ] && clip_dash_applies "${raw}"; then
        if ! clip_dash_prepare "${raw}"; then
            clip_dash_cleanup
            return 1
        fi
    fi

    log_info "Recortando ${CLIP_START} +${CLIP_DURATION}s (re-codificación exacta)..."
    if ! _clip_run_ffmpeg; then
        # Un archivo a medias no sirve y confunde; se elimina
        rm -f "${CLIP_OUTPUT}"
        clip_dash_cleanup; clip_hls_cleanup
        log_error "ffmpeg falló al recortar el tramo."
        return 1
    fi
    clip_dash_cleanup; clip_hls_cleanup

    _clip_verify || return 1
    log_ok "Clip guardado: ${CLIP_OUTPUT}"
    return 0
}
