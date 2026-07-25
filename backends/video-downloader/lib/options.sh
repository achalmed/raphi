#!/usr/bin/env bash
# =============================================================================
#  lib/options.sh — Traductor de intención → argumentos de yt-dlp
# =============================================================================
#
#  Responsabilidad única: convertir las opciones del usuario (OPT_*) y los
#  valores de config.sh en el array global YTDLP_ARGS, que main.sh pasa a
#  yt-dlp. Se usa un ARRAY (no un string) para que rutas, plantillas y
#  cadenas de formato con espacios lleguen intactas y sin necesidad de eval.
#
#  Cada _opts_* anexa su fragmento; build_ytdlp_args las orquesta según el modo.
# =============================================================================

# Array global que se rellena aquí y se consume en lib/downloader.sh
YTDLP_ARGS=()

# ── _opts_format() ───────────────────────────────────────────────────────────
# Selección de formato de video/audio según modo, calidad y contenedor.
# Precedencia: --format crudo > modo audio > modo best > altura numérica.
_opts_format() {
    if [ -n "${OPT_FORMAT}" ]; then
        YTDLP_ARGS+=( -f "${OPT_FORMAT}" )
        return 0
    fi

    if [ "${OPT_MODE}" = "audio" ]; then
        # Preferir la mejor pista solo-audio; -x/--audio-* los añade _opts_audio
        YTDLP_ARGS+=( -f "bestaudio/best" )
        return 0
    fi

    # best, o quality=best/worst → dejar el selector amplio; si no, limitar altura
    if [ "${OPT_MODE}" = "best" ] || [ "${OPT_QUALITY}" = "best" ]; then
        YTDLP_ARGS+=( -f "bv*+ba/b" )
    elif [ "${OPT_QUALITY}" = "worst" ]; then
        YTDLP_ARGS+=( -f "wv*+wa/w" )
    else
        # <=? no falla si la altura del stream es desconocida; cadena de reserva al final
        local h="${OPT_QUALITY}"
        YTDLP_ARGS+=( -f "bv*[height<=?${h}]+ba/b[height<=?${h}]/bv*+ba/b" )
    fi

    # Contenedor de salida al fusionar (solo aplica a modos con video)
    YTDLP_ARGS+=( --merge-output-format "${OPT_CONTAINER}" )
}

# ── _opts_audio() ────────────────────────────────────────────────────────────
# Extracción de audio (solo modo audio): -x + formato + calidad.
_opts_audio() {
    [ "${OPT_MODE}" = "audio" ] || return 0
    YTDLP_ARGS+=( -x --audio-format "${OPT_AUDIO_FORMAT}" --audio-quality "${OPT_AUDIO_QUALITY}" )
}

# ── _opts_subs() ─────────────────────────────────────────────────────────────
# Subtítulos: descarga, autogenerados, idiomas, incrustado y formato.
_opts_subs() {
    # En modo subs siempre se activan aunque no se pase --subs
    if [ "${OPT_MODE}" = "subs" ]; then
        OPT_SUBS=true
    fi
    [ "${OPT_SUBS}" = true ] || [ "${OPT_AUTO_SUBS}" = true ] || return 0

    [ "${OPT_SUBS}" = true ]      && YTDLP_ARGS+=( --write-subs )
    [ "${OPT_AUTO_SUBS}" = true ] && YTDLP_ARGS+=( --write-auto-subs )
    YTDLP_ARGS+=( --sub-langs "${OPT_SUB_LANGS}" --sub-format "${DEFAULT_SUB_FORMAT}" )

    if [ "${OPT_EMBED_SUBS}" = true ]; then
        YTDLP_ARGS+=( --embed-subs )
    else
        # Sin incrustar: convertir al formato pedido para archivos .srt limpios
        YTDLP_ARGS+=( --convert-subs "${DEFAULT_SUB_FORMAT}" )
    fi
}

# ── _opts_metadata() ─────────────────────────────────────────────────────────
# Metadatos, capítulos, miniatura y volcados a disco.
_opts_metadata() {
    [ "${OPT_EMBED_METADATA}" = true ]  && YTDLP_ARGS+=( --embed-metadata )
    [ "${OPT_EMBED_CHAPTERS}" = true ]  && YTDLP_ARGS+=( --embed-chapters )
    [ "${OPT_EMBED_THUMBNAIL}" = true ] && YTDLP_ARGS+=( --embed-thumbnail )
    [ "${OPT_WRITE_THUMBNAIL}" = true ] && YTDLP_ARGS+=( --write-thumbnail )
    [ "${OPT_WRITE_INFO_JSON}" = true ] && YTDLP_ARGS+=( --write-info-json )
    # return explícito: si el último test es falso, la función devolvería 1
    # y set -e abortaría el script en el llamador.
    return 0
}

# ── _opts_sponsorblock() ─────────────────────────────────────────────────────
# Recorta segmentos (patrocinios, intros, etc.) usando la API de SponsorBlock.
_opts_sponsorblock() {
    [ "${OPT_SPONSORBLOCK}" = true ] || return 0
    YTDLP_ARGS+=( --sponsorblock-remove "${SPONSORBLOCK_CATEGORIES}" )
}

# ── _opts_playlist() ─────────────────────────────────────────────────────────
# Control de playlists: single vs. completa, selección de items y tope.
_opts_playlist() {
    if [ "${OPT_NO_PLAYLIST}" = true ]; then
        YTDLP_ARGS+=( --no-playlist )
    else
        YTDLP_ARGS+=( --yes-playlist )
    fi
    [ -n "${OPT_PLAYLIST_ITEMS}" ] && YTDLP_ARGS+=( -I "${OPT_PLAYLIST_ITEMS}" )
    # OPT_MAX_DOWNLOADS ya se validó como numérico en cli.sh
    [ "${OPT_MAX_DOWNLOADS}" -gt 0 ] && YTDLP_ARGS+=( --max-downloads "${OPT_MAX_DOWNLOADS}" )
    return 0   # ver nota de set -e en _opts_metadata
}

# ── _opts_network() ──────────────────────────────────────────────────────────
# Reintentos, concurrencia, límite de tasa, espera, aria2c, proxy y cookies.
_opts_network() {
    YTDLP_ARGS+=( --retries "${OPT_RETRIES}" --fragment-retries "${OPT_RETRIES}" )
    YTDLP_ARGS+=( --concurrent-fragments "${OPT_CONCURRENT}" )
    [ -n "${OPT_RATE_LIMIT}" ] && YTDLP_ARGS+=( --limit-rate "${OPT_RATE_LIMIT}" )
    [ "${OPT_SLEEP}" != "0" ]  && YTDLP_ARGS+=( --sleep-interval "${OPT_SLEEP}" )

    if [ "${OPT_USE_ARIA2}" = true ]; then
        # aria2c abre múltiples conexiones por descarga; acelera mucho en redes lentas
        YTDLP_ARGS+=( --downloader aria2c --downloader-args "aria2c:-x16 -s16 -k1M" )
    fi

    [ -n "${OPT_PROXY}" ]              && YTDLP_ARGS+=( --proxy "${OPT_PROXY}" )
    [ -n "${OPT_USER_AGENT}" ]        && YTDLP_ARGS+=( --user-agent "${OPT_USER_AGENT}" )
    [ -n "${OPT_COOKIES_FILE}" ]      && YTDLP_ARGS+=( --cookies "${OPT_COOKIES_FILE}" )
    [ -n "${OPT_COOKIES_BROWSER}" ]   && YTDLP_ARGS+=( --cookies-from-browser "${OPT_COOKIES_BROWSER}" )
    return 0   # ver nota de set -e en _opts_metadata
}

# ── _opts_output() ───────────────────────────────────────────────────────────
# Carpeta de destino, plantilla de nombre y opciones de sistema de archivos.
_opts_output() {
    YTDLP_ARGS+=( -P "${OPT_OUTPUT_DIR}" )

    local template
    if [ -n "${OPT_TEMPLATE}" ]; then
        template="${OPT_TEMPLATE}"
    elif [ "${OPT_ORGANIZE}" = true ]; then
        template="${OUTPUT_TEMPLATE_ORGANIZED}"
    else
        template="${OUTPUT_TEMPLATE}"
    fi
    YTDLP_ARGS+=( -o "${template}" )

    [ "${OPT_RESTRICT_NAMES}" = true ] && YTDLP_ARGS+=( --restrict-filenames )
    # Continuar descargas parciales y no re-descargar lo existente
    YTDLP_ARGS+=( --continue --no-overwrites )
}

# ── _opts_archive() ──────────────────────────────────────────────────────────
# Historial persistente: yt-dlp salta lo que ya figure en el archivo.
_opts_archive() {
    [ "${OPT_ARCHIVE}" = true ] || return 0
    mkdir -p "$(dirname "${ARCHIVE_FILE}")"
    YTDLP_ARGS+=( --download-archive "${ARCHIVE_FILE}" )
}

# ── _opts_misc() ─────────────────────────────────────────────────────────────
# Verbosidad, simulación, y los passthrough --extra / EXTRA_YTDLP_OPTS.
_opts_misc() {
    # Siempre ignorar errores de un item para no abortar todo el lote
    YTDLP_ARGS+=( --ignore-errors )

    if [ "${OPT_VERBOSE}" = true ]; then
        YTDLP_ARGS+=( --verbose )
    else
        YTDLP_ARGS+=( --no-warnings --quiet --progress )
    fi

    [ "${OPT_SIMULATE}" = true ] && YTDLP_ARGS+=( --simulate )

    # Passthrough: primero el array de config, luego la cadena --extra (word-split)
    if [ "${#EXTRA_YTDLP_OPTS[@]}" -gt 0 ]; then
        YTDLP_ARGS+=( "${EXTRA_YTDLP_OPTS[@]}" )
    fi
    if [ -n "${OPT_EXTRA}" ]; then
        # Split simple por espacios; para citas complejas usar EXTRA_YTDLP_OPTS en config
        local -a extra_tokens
        read -ra extra_tokens <<< "${OPT_EXTRA}"
        YTDLP_ARGS+=( "${extra_tokens[@]}" )
    fi
}

# ── build_ytdlp_args() ───────────────────────────────────────────────────────
# Orquesta el ensamblado del array YTDLP_ARGS para los modos de descarga
# (video/audio/best/subs). Los modos info/formats usan build_info_args.
build_ytdlp_args() {
    YTDLP_ARGS=()
    _opts_output
    _opts_format
    _opts_audio
    _opts_subs
    _opts_metadata
    _opts_sponsorblock
    _opts_playlist
    _opts_network
    _opts_archive
    _opts_misc

    # Modo subs: no descargar el video, solo los subtítulos
    [ "${OPT_MODE}" = "subs" ] && YTDLP_ARGS+=( --skip-download )
    return 0   # ver nota de set -e en _opts_metadata
}

# ── build_info_args() ────────────────────────────────────────────────────────
# Conjunto mínimo para los modos info/formats: solo acceso a la red y playlist,
# sin opciones de descarga/formato que aquí no aplican.
build_info_args() {
    YTDLP_ARGS=()
    _opts_playlist
    _opts_network
    YTDLP_ARGS+=( --ignore-errors )
    [ "${OPT_VERBOSE}" = true ] && YTDLP_ARGS+=( --verbose )
    return 0   # ver nota de set -e en _opts_metadata
}
