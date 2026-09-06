#!/usr/bin/env bash
# =============================================================================
#  config.sh — Configuración centralizada de video-downloader
# =============================================================================
#
#  TODO valor ajustable del script vive aquí. Edita este archivo para cambiar
#  el comportamiento por defecto sin tocar la lógica de ningún módulo de lib/.
#
#  El motor real es yt-dlp; ffmpeg se usa para fusionar/convertir. Las opciones
#  se traducen a flags de yt-dlp en lib/options.sh. Cualquier capacidad de
#  yt-dlp no envuelta aquí es alcanzable vía --extra o EXTRA_YTDLP_OPTS.
# =============================================================================

# ── Usuario y rutas base ─────────────────────────────────────────────────────
USUARIO="${SUDO_USER:-${USER:-achalmaedison}}"
HOME_DIR="/home/${USUARIO}"

# ── Carpeta de destino de las descargas ──────────────────────────────────────
# Se crea automáticamente si no existe. Sobreescribible con --output-dir/-o.
DEFAULT_OUTPUT_DIR="${HOME_DIR}/Downloads/videos"

# ── Modo de descarga ─────────────────────────────────────────────────────────
#   video    — mejor video+audio hasta la calidad elegida, fusionado
#   audio    — solo audio, extraído al formato DEFAULT_AUDIO_FORMAT
#   best     — la mejor calidad absoluta disponible (ignora --quality)
#   info     — no descarga; imprime metadatos (usa jq si está disponible)
#   formats  — no descarga; lista los formatos disponibles del video
#   subs     — no descarga el video; solo baja subtítulos
DEFAULT_MODE="video"

# ── Calidad de video (altura máxima en px, o best/worst) ─────────────────────
# Ej.: 2160 (4K), 1440 (2K), 1080, 720, 480, 360, best, worst.
DEFAULT_QUALITY="best"

# ── Contenedor de salida al fusionar video+audio ─────────────────────────────
# mp4 es el más compatible; mkv admite cualquier códec/subtítulo; webm es libre.
DEFAULT_CONTAINER="mp4"

# ── Cadena -f cruda de yt-dlp (usuarios avanzados) ───────────────────────────
# Si se define (o se pasa --format), tiene precedencia sobre --quality.
DEFAULT_FORMAT=""

# ── Extracción de audio (modo audio) ─────────────────────────────────────────
# Formato: mp3|m4a|opus|flac|wav|vorbis|aac|best
DEFAULT_AUDIO_FORMAT="mp3"
# Calidad: 0 = mejor VBR ... 10 = peor; o un bitrate fijo como 192K.
DEFAULT_AUDIO_QUALITY="0"

# ── Subtítulos ───────────────────────────────────────────────────────────────
DEFAULT_SUBS=false            # descargar subtítulos manuales
DEFAULT_AUTO_SUBS=false       # incluir subtítulos autogenerados
DEFAULT_EMBED_SUBS=false      # incrustarlos en el contenedor (mkv/mp4)
DEFAULT_SUB_LANGS="es,en"     # idiomas (coma-separados); "all" para todos
DEFAULT_SUB_FORMAT="srt"      # srt|vtt|ass|best

# ── Metadatos, miniatura y capítulos ─────────────────────────────────────────
DEFAULT_EMBED_METADATA=true   # título/autor/fecha dentro del archivo
DEFAULT_EMBED_CHAPTERS=true   # capítulos como marcadores del contenedor
DEFAULT_EMBED_THUMBNAIL=false # carátula incrustada (mp4 requiere AtomicParsley)
DEFAULT_WRITE_THUMBNAIL=false # guardar la miniatura como archivo aparte
DEFAULT_WRITE_INFO_JSON=false # guardar el .info.json con todos los metadatos

# ── SponsorBlock (recorta segmentos patrocinados, intros, etc.) ──────────────
DEFAULT_SPONSORBLOCK=false
# Categorías a eliminar: sponsor,selfpromo,interaction,intro,outro,preview,music_offtopic
SPONSORBLOCK_CATEGORIES="sponsor,selfpromo,interaction"

# ── Playlists ────────────────────────────────────────────────────────────────
DEFAULT_NO_PLAYLIST=false     # true = de una URL de playlist baja solo el video
DEFAULT_ORGANIZE=false        # crear subcarpetas por uploader/playlist
DEFAULT_PLAYLIST_ITEMS=""     # selección: "1:10", "1,3,5", "2:-1" (ver -I de yt-dlp)
DEFAULT_MAX_DOWNLOADS=0       # 0 = sin límite

# ── Archivo de historial (no volver a descargar lo ya bajado) ────────────────
DEFAULT_ARCHIVE=false
ARCHIVE_FILE="${HOME_DIR}/.local/share/video_downloader/descargados.txt"

# ── Red y robustez ───────────────────────────────────────────────────────────
DEFAULT_RETRIES=10            # reintentos por fragmento/descarga
DEFAULT_CONCURRENT=4          # fragmentos descargados en paralelo (yt-dlp -N)
DEFAULT_RATE_LIMIT=""         # límite de velocidad, ej. "2M"; vacío = sin límite
DEFAULT_SLEEP=0               # segundos de espera entre videos (cortesía anti-bloqueo)
DEFAULT_USE_ARIA2=false       # usar aria2c como descargador externo (si está instalado)
DEFAULT_RESTRICT_NAMES=false  # nombres de archivo ASCII-safe (sin espacios ni tildes)

# ── Recorte exacto de tramos (--clip INICIO-FIN) ─────────────────────────────
# El clip se re-codifica con ffmpeg para garantizar corte exacto y A/V en
# sincronía (ver lib/clipper.sh). Estos valores controlan esa re-codificación.
CLIP_VIDEO_CRF=20             # calidad x264: 18 (más calidad) … 28 (más liviano)
CLIP_VIDEO_PRESET="veryfast"  # velocidad de codificación: ultrafast…slow
CLIP_AUDIO_BITRATE="128k"     # bitrate AAC del clip
# Prefijo de respaldo para el nombre del archivo cuando el sitio devuelve un
# título vacío o inservible (p. ej. Facebook a veces devuelve un solo "."):
# el nombre pasaría a ser "<prefijo>_<fecha>_<hora>" en vez de un dotfile oculto.
CLIP_FALLBACK_PREFIX="clip"

# ── Autenticación / acceso ───────────────────────────────────────────────────
# Muchos videos de Facebook/Instagram/privados requieren cookies de sesión.
COOKIES_FILE=""               # ruta a un cookies.txt exportado
COOKIES_FROM_BROWSER=""       # firefox|chrome|chromium|brave|edge|opera|vivaldi
PROXY=""                      # ej. "socks5://127.0.0.1:9050" o "http://host:port"
USER_AGENT=""                 # User-Agent personalizado (vacío = el de yt-dlp)

# ── Plantillas de nombre de salida (sintaxis de yt-dlp -o) ───────────────────
OUTPUT_TEMPLATE="%(title)s [%(id)s].%(ext)s"
OUTPUT_TEMPLATE_ORGANIZED="%(uploader).80B/%(playlist_title|Sueltos)s/%(title)s [%(id)s].%(ext)s"

# ── Flags crudas extra para yt-dlp (casos avanzados) ─────────────────────────
# Todo lo que no esté envuelto por una flag propia va aquí, un elemento por token.
# Ej.: EXTRA_YTDLP_OPTS=( "--geo-bypass-country" "US" "--force-ipv4" )
EXTRA_YTDLP_OPTS=()

# ── Archivo de log ───────────────────────────────────────────────────────────
LOG_FILE="${HOME_DIR}/video_downloader.log"
LOG_MAX_BYTES=10485760        # 10 MB — rota automáticamente al superarlo

# ── Valores por defecto de flags generales ───────────────────────────────────
DEFAULT_VERBOSE=false
DEFAULT_SIMULATE=false        # --simulate de yt-dlp: hace todo menos descargar
DEFAULT_LOG=false
DEFAULT_NO_CONFIRM=false
