#!/usr/bin/env bash
# =============================================================================
#  lib/cli.sh — Interfaz de línea de comandos
# =============================================================================
#
#  Define y parsea todos los flags. Centralizar el CLI aquí mantiene main.sh
#  limpio y hace trivial agregar flags nuevas sin tocar la lógica de negocio.
#
#  Los OPT_* se inicializan desde los DEFAULT_* de config.sh (que se carga
#  antes que este módulo), de modo que el único lugar para cambiar defaults
#  sigue siendo config.sh.
# =============================================================================

# ── Estado de opciones (inicializado desde config.sh) ────────────────────────
OPT_VERBOSE="${DEFAULT_VERBOSE}"
OPT_SIMULATE="${DEFAULT_SIMULATE}"
OPT_LOG="${DEFAULT_LOG}"
OPT_NO_CONFIRM="${DEFAULT_NO_CONFIRM}"

OPT_MODE="${DEFAULT_MODE}"
OPT_QUALITY="${DEFAULT_QUALITY}"
OPT_CONTAINER="${DEFAULT_CONTAINER}"
OPT_FORMAT="${DEFAULT_FORMAT}"
OPT_OUTPUT_DIR="${DEFAULT_OUTPUT_DIR}"
OPT_TEMPLATE=""

OPT_AUDIO_FORMAT="${DEFAULT_AUDIO_FORMAT}"
OPT_AUDIO_QUALITY="${DEFAULT_AUDIO_QUALITY}"

OPT_SUBS="${DEFAULT_SUBS}"
OPT_AUTO_SUBS="${DEFAULT_AUTO_SUBS}"
OPT_EMBED_SUBS="${DEFAULT_EMBED_SUBS}"
OPT_SUB_LANGS="${DEFAULT_SUB_LANGS}"

OPT_EMBED_METADATA="${DEFAULT_EMBED_METADATA}"
OPT_EMBED_CHAPTERS="${DEFAULT_EMBED_CHAPTERS}"
OPT_EMBED_THUMBNAIL="${DEFAULT_EMBED_THUMBNAIL}"
OPT_WRITE_THUMBNAIL="${DEFAULT_WRITE_THUMBNAIL}"
OPT_WRITE_INFO_JSON="${DEFAULT_WRITE_INFO_JSON}"
OPT_SPONSORBLOCK="${DEFAULT_SPONSORBLOCK}"

OPT_NO_PLAYLIST="${DEFAULT_NO_PLAYLIST}"
OPT_ORGANIZE="${DEFAULT_ORGANIZE}"
OPT_PLAYLIST_ITEMS="${DEFAULT_PLAYLIST_ITEMS}"
OPT_MAX_DOWNLOADS="${DEFAULT_MAX_DOWNLOADS}"

OPT_ARCHIVE="${DEFAULT_ARCHIVE}"
OPT_RETRIES="${DEFAULT_RETRIES}"
OPT_CONCURRENT="${DEFAULT_CONCURRENT}"
OPT_RATE_LIMIT="${DEFAULT_RATE_LIMIT}"
OPT_SLEEP="${DEFAULT_SLEEP}"
OPT_USE_ARIA2="${DEFAULT_USE_ARIA2}"
OPT_RESTRICT_NAMES="${DEFAULT_RESTRICT_NAMES}"

OPT_COOKIES_FILE="${COOKIES_FILE}"
OPT_COOKIES_BROWSER="${COOKIES_FROM_BROWSER}"
OPT_PROXY="${PROXY}"
OPT_USER_AGENT="${USER_AGENT}"

OPT_BATCH_FILE=""
OPT_POST_CMD=""
OPT_EXTRA=""
OPT_UPDATE=false
OPT_CLIP=""

# URLs posicionales acumuladas durante el parseo
OPT_URLS=()

# ── _require_value() ─────────────────────────────────────────────────────────
# Aborta con mensaje claro si una flag que exige valor no lo recibió.
# Bajo `set -u`, leer un $2 ausente mata el script con un error críptico.
#
# Arguments:
#   $1 - Nombre de la flag (para el mensaje)
#   $2 - Valor recibido (posiblemente vacío)
_require_value() {
    if [ -z "${2:-}" ]; then
        log_error "${1} requiere un valor."
        exit 2
    fi
}

# ── show_version() ───────────────────────────────────────────────────────────
show_version() {
    echo "video-downloader v1.1.1"
    echo "Wrapper modular de yt-dlp — YouTube, Facebook y ~1800 sitios más"
    echo "Autor: achalmaedison"
}

# ── show_help() ──────────────────────────────────────────────────────────────
# Ayuda completa con colores si el terminal los soporta.
show_help() {
    cat <<EOF
${CLR_BOLD}${CLR_BLUE}
╔══════════════════════════════════════════════════════════════════════╗
║        VIDEO-DOWNLOADER — Descargador universal (yt-dlp)              ║
║        YouTube · Facebook · Instagram · TikTok · Vimeo · y más       ║
╚══════════════════════════════════════════════════════════════════════╝
${CLR_RESET}
${CLR_BOLD}USO:${CLR_RESET}
    $(basename "$0") [OPCIONES] URL [URL2 ...]
    $(basename "$0") [OPCIONES] --batch lista_urls.txt

${CLR_BOLD}GENERALES:${CLR_RESET}
    -h, --help              Muestra esta ayuda y sale
        --version           Muestra la versión
    -v, --verbose           Modo detallado (salida ampliada de yt-dlp)
    -s, --simulate          Simula: hace todo menos descargar (dry-run)
    -l, --log               Guarda log en: ${LOG_FILE}
        --no-confirm        No pide confirmación inicial (cron/scripts)
        --update            Actualiza yt-dlp (yt-dlp -U) y sale

${CLR_BOLD}MODO Y CALIDAD:${CLR_RESET}
    -m, --mode <modo>       video|audio|best|info|formats|subs  (def: ${DEFAULT_MODE})
    -q, --quality <q>       Altura máx: 2160|1440|1080|720|480|360|best|worst
    -c, --container <c>     mp4|mkv|webm  (contenedor al fusionar; def: ${DEFAULT_CONTAINER})
    -f, --format <str>      Cadena -f cruda de yt-dlp (avanzado; ignora --quality)

${CLR_BOLD}RECORTE EXACTO DE TRAMOS:${CLR_RESET}
        --clip <INI-FIN>    Recorta solo ese tramo, con corte exacto y
                            verificación automática (formatos: H:MM:SS,
                            MM:SS o SS). Compatible con modos video/best/audio.
                            Ej.: --clip 2:46:00-2:47:00

${CLR_BOLD}AUDIO (modo audio):${CLR_RESET}
        --audio-format <f>  mp3|m4a|opus|flac|wav|vorbis|aac|best  (def: ${DEFAULT_AUDIO_FORMAT})
        --audio-quality <q> 0 (mejor) … 10 (peor), o bitrate como 192K

${CLR_BOLD}SALIDA:${CLR_RESET}
    -o, --output-dir <dir>  Carpeta de destino (def: ${DEFAULT_OUTPUT_DIR})
    -t, --template <tpl>    Plantilla de nombre yt-dlp (avanzado)
        --organize          Subcarpetas por uploader/playlist
        --restrict-names    Nombres ASCII-safe (sin espacios ni tildes)

${CLR_BOLD}SUBTÍTULOS:${CLR_RESET}
        --subs              Descarga subtítulos manuales
        --auto-subs         Incluye subtítulos autogenerados
        --embed-subs        Incrusta los subtítulos en el archivo
        --sub-langs <lista> Idiomas coma-separados o 'all'  (def: ${DEFAULT_SUB_LANGS})

${CLR_BOLD}METADATOS Y EXTRAS:${CLR_RESET}
        --thumbnail         Incrusta la miniatura como carátula
        --write-thumbnail   Guarda la miniatura como archivo aparte
        --write-info        Guarda el .info.json con todos los metadatos
        --no-metadata       No incrustar metadatos
        --no-chapters       No incrustar capítulos
        --sponsorblock      Recorta segmentos (${SPONSORBLOCK_CATEGORIES})

${CLR_BOLD}PLAYLISTS:${CLR_RESET}
        --no-playlist       De una URL de playlist, baja solo el video
        --items <sel>       Selección: "1:10" | "1,3,5" | "2:-1"
        --max <n>           Máximo de descargas (0 = sin límite)

${CLR_BOLD}RED Y ROBUSTEZ:${CLR_RESET}
        --archive           Salta lo ya descargado (historial persistente)
        --retries <n>       Reintentos (def: ${DEFAULT_RETRIES})
    -N, --concurrent <n>    Fragmentos en paralelo (def: ${DEFAULT_CONCURRENT})
        --rate-limit <r>    Límite de velocidad, ej. 2M
        --sleep <seg>       Espera entre videos (cortesía anti-bloqueo)
        --aria2             Usa aria2c como descargador externo (si está)

${CLR_BOLD}ACCESO (contenido privado/con login):${CLR_RESET}
        --cookies <archivo>       Archivo cookies.txt exportado
        --cookies-browser <nav>   firefox|chrome|brave|edge|opera|vivaldi
        --proxy <url>             Proxy, ej. socks5://127.0.0.1:9050
        --user-agent <ua>         User-Agent personalizado

${CLR_BOLD}ESCAPE (cualquier flag de yt-dlp no envuelta):${CLR_RESET}
        --extra "<flags>"   Se anexan tal cual a yt-dlp (o edita EXTRA_YTDLP_OPTS)

${CLR_BOLD}EJEMPLOS:${CLR_RESET}
    # Video en la mejor calidad hasta 1080p, contenedor mp4
    $(basename "$0") -q 1080 https://youtu.be/XXXX

    # Solo audio en mp3 de máxima calidad
    $(basename "$0") -m audio --audio-format mp3 https://youtu.be/XXXX

    # Playlist completa con subtítulos incrustados, organizada en subcarpetas
    $(basename "$0") --organize --subs --embed-subs https://youtube.com/playlist?list=YYYY

    # Descarga por lotes desde un archivo, sin re-descargar lo ya bajado
    $(basename "$0") --archive --batch urls.txt

    # Video de Facebook privado usando cookies del navegador
    $(basename "$0") --cookies-browser firefox https://www.facebook.com/watch?v=ZZZZ

    # Recortar un tramo exacto (min 2:46:00 al 2:47:00) de un video de Facebook
    $(basename "$0") --clip 2:46:00-2:47:00 https://www.facebook.com/watch?v=ZZZZ

    # Ver los formatos disponibles sin descargar
    $(basename "$0") -m formats https://youtu.be/XXXX

    # Metadatos del video en JSON (sin descargar)
    $(basename "$0") -m info https://youtu.be/XXXX

    # Máxima calidad + miniatura + SponsorBlock, con simulación previa
    $(basename "$0") -m best --thumbnail --sponsorblock -s https://youtu.be/XXXX

${CLR_BOLD}DESTINO POR DEFECTO:${CLR_RESET} ${DEFAULT_OUTPUT_DIR}/
EOF
}

# ── parse_args() ─────────────────────────────────────────────────────────────
# Parsea todos los argumentos. Flags cortos y largos vía case; lo que no sea
# flag se acumula como URL posicional en OPT_URLS.
#
# Arguments:
#   $@ - Todos los argumentos del script
# Returns:
#   0 en éxito; exit 0 en --help/--version; exit 2 en error de uso
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)             show_help; exit 0 ;;
            --version)             show_version; exit 0 ;;
            -v|--verbose)          OPT_VERBOSE=true; shift ;;
            -s|--simulate)         OPT_SIMULATE=true; shift ;;
            -l|--log)              OPT_LOG=true; shift ;;
            --no-confirm)          OPT_NO_CONFIRM=true; shift ;;
            --update)              OPT_UPDATE=true; shift ;;

            -m|--mode)             _require_value "--mode" "${2:-}"; OPT_MODE="$2"; shift 2 ;;
            -q|--quality)          _require_value "--quality" "${2:-}"; OPT_QUALITY="$2"; shift 2 ;;
            -c|--container)        _require_value "--container" "${2:-}"; OPT_CONTAINER="$2"; shift 2 ;;
            -f|--format)           _require_value "--format" "${2:-}"; OPT_FORMAT="$2"; shift 2 ;;
            -o|--output-dir)       _require_value "--output-dir" "${2:-}"; OPT_OUTPUT_DIR="$2"; shift 2 ;;
            -t|--template)         _require_value "--template" "${2:-}"; OPT_TEMPLATE="$2"; shift 2 ;;

            --audio-format)        _require_value "--audio-format" "${2:-}"; OPT_AUDIO_FORMAT="$2"; shift 2 ;;
            --audio-quality)       _require_value "--audio-quality" "${2:-}"; OPT_AUDIO_QUALITY="$2"; shift 2 ;;

            --organize)            OPT_ORGANIZE=true; shift ;;
            --restrict-names)      OPT_RESTRICT_NAMES=true; shift ;;

            --subs)                OPT_SUBS=true; shift ;;
            --auto-subs)           OPT_AUTO_SUBS=true; shift ;;
            --embed-subs)          OPT_EMBED_SUBS=true; shift ;;
            --sub-langs)           _require_value "--sub-langs" "${2:-}"; OPT_SUB_LANGS="$2"; shift 2 ;;

            --thumbnail)           OPT_EMBED_THUMBNAIL=true; shift ;;
            --write-thumbnail)     OPT_WRITE_THUMBNAIL=true; shift ;;
            --write-info)          OPT_WRITE_INFO_JSON=true; shift ;;
            --no-metadata)         OPT_EMBED_METADATA=false; shift ;;
            --no-chapters)         OPT_EMBED_CHAPTERS=false; shift ;;
            --sponsorblock)        OPT_SPONSORBLOCK=true; shift ;;

            --no-playlist)         OPT_NO_PLAYLIST=true; shift ;;
            --items)               _require_value "--items" "${2:-}"; OPT_PLAYLIST_ITEMS="$2"; shift 2 ;;
            --max)                 _require_value "--max" "${2:-}"; OPT_MAX_DOWNLOADS="$2"; shift 2 ;;

            --archive)             OPT_ARCHIVE=true; shift ;;
            --retries)             _require_value "--retries" "${2:-}"; OPT_RETRIES="$2"; shift 2 ;;
            -N|--concurrent)       _require_value "--concurrent" "${2:-}"; OPT_CONCURRENT="$2"; shift 2 ;;
            --rate-limit)          _require_value "--rate-limit" "${2:-}"; OPT_RATE_LIMIT="$2"; shift 2 ;;
            --sleep)               _require_value "--sleep" "${2:-}"; OPT_SLEEP="$2"; shift 2 ;;
            --aria2)               OPT_USE_ARIA2=true; shift ;;

            --cookies)             _require_value "--cookies" "${2:-}"; OPT_COOKIES_FILE="$2"; shift 2 ;;
            --cookies-browser)     _require_value "--cookies-browser" "${2:-}"; OPT_COOKIES_BROWSER="$2"; shift 2 ;;
            --proxy)               _require_value "--proxy" "${2:-}"; OPT_PROXY="$2"; shift 2 ;;
            --user-agent)          _require_value "--user-agent" "${2:-}"; OPT_USER_AGENT="$2"; shift 2 ;;

            --clip)                _require_value "--clip" "${2:-}"; OPT_CLIP="$2"; shift 2 ;;
            --batch)               _require_value "--batch" "${2:-}"; OPT_BATCH_FILE="$2"; shift 2 ;;
            --post-cmd)            _require_value "--post-cmd" "${2:-}"; OPT_POST_CMD="$2"; shift 2 ;;
            --extra)               _require_value "--extra" "${2:-}"; OPT_EXTRA="$2"; shift 2 ;;

            --)                    shift; while [[ $# -gt 0 ]]; do OPT_URLS+=("$1"); shift; done ;;
            -*)
                log_error "Argumento desconocido: '$1'"
                log_error "Usa --help para ver las opciones disponibles."
                exit 2 ;;
            *)                     OPT_URLS+=("$1"); shift ;;
        esac
    done

    _validate_flag_combinations
}

# ── _validate_flag_combinations() ────────────────────────────────────────────
# Detecta combinaciones inválidas o incoherentes tras el parseo.
_validate_flag_combinations() {
    # Modo válido
    case "${OPT_MODE}" in
        video|audio|best|info|formats|subs) ;;
        *)
            log_error "Modo inválido: '${OPT_MODE}'. Usa: video|audio|best|info|formats|subs"
            exit 2 ;;
    esac

    # Contenedor válido
    case "${OPT_CONTAINER}" in
        mp4|mkv|webm) ;;
        *)
            log_error "Contenedor inválido: '${OPT_CONTAINER}'. Usa: mp4|mkv|webm"
            exit 2 ;;
    esac

    # --embed-subs implica descargar subs
    if [ "${OPT_EMBED_SUBS}" = true ]; then
        OPT_SUBS=true
    fi

    # cookies-file y cookies-browser son mutuamente excluyentes en yt-dlp
    if [ -n "${OPT_COOKIES_FILE}" ] && [ -n "${OPT_COOKIES_BROWSER}" ]; then
        log_error "--cookies y --cookies-browser no pueden usarse a la vez."
        exit 2
    fi

    # --clip re-codifica con ffmpeg: solo tiene sentido en modos con descarga
    if [ -n "${OPT_CLIP}" ]; then
        case "${OPT_MODE}" in
            video|best|audio) ;;
            *)
                log_error "--clip solo es compatible con los modos video, best y audio."
                exit 2 ;;
        esac
    fi

    # Valores que deben ser enteros: evita errores crípticos de [ -gt ] después
    _require_integer "--max"        "${OPT_MAX_DOWNLOADS}"
    _require_integer "--retries"    "${OPT_RETRIES}"
    _require_integer "--concurrent" "${OPT_CONCURRENT}"
    _require_integer "--sleep"      "${OPT_SLEEP}"
}

# ── _require_integer() ───────────────────────────────────────────────────────
# Aborta si el valor de una flag numérica no es un entero no negativo.
#
# Arguments:
#   $1 - Nombre de la flag (para el mensaje)
#   $2 - Valor a comprobar
_require_integer() {
    case "$2" in
        ''|*[!0-9]*)
            log_error "$1 requiere un número entero; se recibió: '$2'"
            exit 2 ;;
    esac
}
