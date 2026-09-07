# video-downloader — Descargador universal de video/audio

<!-- suite:inicio -->
**Suite `video_downloader`** · objetivo *multimedia* · estado *activo* · bash · interfaz cli

Descarga video o audio con yt-dlp y ffmpeg, por URL o por lotes, con recorte opcional.

- Escribe en: archivos · simula por defecto: no
- Depende de: yt-dlp, ffmpeg

Comandos:

```bash
main.sh <url>
main.sh --audio <url>
main.sh --batch lista.txt
main.sh --simulate <url>
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-09-07); no se edita a mano.</sub>
<!-- suite:fin -->

> Wrapper modular de `yt-dlp` para descargar video y audio de YouTube,
> Facebook, Instagram, TikTok, Vimeo, X/Twitter y ~1800 sitios más, con
> selección de calidad, subtítulos, playlists, lotes, historial,
> SponsorBlock y recorte exacto de tramos (`--clip`) con verificación
> automática — todo desde una CLI en español.

---

## 📋 Tabla de Contenidos

- [Descripción](#-descripción)
- [Requisitos](#️-requisitos)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Modos de operación](#️-modos-de-operación)
- [Casos de uso frecuentes](#-casos-de-uso-frecuentes)
- [Arquitectura](#️-arquitectura)
- [Solución de Problemas](#-solución-de-problemas)
- [Cómo Agregar Funcionalidades](#-cómo-agregar-funcionalidades)
- [Notas y Advertencias](#️-notas-y-advertencias)

---

## 📖 Descripción

`video-downloader` orquesta `yt-dlp` (el sucesor activo de youtube-dl) y
`ffmpeg` detrás de una interfaz coherente con el resto de herramientas de
`scripts_for_linux`: flags en español, confirmación interactiva, modo
simulación, log con rotación y resumen final con contadores.

**Qué aporta sobre llamar a yt-dlp directamente:**

- Defaults sensatos centralizados en `config.sh` (calidad, contenedor,
  plantilla de nombres, carpeta destino) — se cambian una vez, no en cada
  invocación.
- Flags legibles (`-m audio`, `-q 1080`, `--subs`) que se traducen a las
  combinaciones correctas de yt-dlp (selectores `-f`, postprocesadores, etc.).
- Procesamiento por lotes con continuación ante errores y balance final.
- Todo lo NO envuelto sigue disponible vía `--extra "<flags>"` o el array
  `EXTRA_YTDLP_OPTS` de `config.sh` — no hay capacidad de yt-dlp inalcanzable.

**Flujo de ejecución:**

```
parse_args → logger → validar (deps, calidad, cookies, destino)
  → reunir objetivos (URLs + --batch) → construir argumentos yt-dlp
  → banner de configuración + confirmación → procesar cada objetivo
  → resumen (éxitos/fallos) → post-comando opcional
```

---

## ⚙️ Requisitos

### Sistema Operativo

- Kubuntu / Ubuntu 22.04+ · Arch Linux / Archcraft
- Bash >= 4.3

### Dependencias

| Paquete         | Tipo                       | Instalación (Arch)       | Instalación (Kubuntu)     |
| --------------- | -------------------------- | ------------------------ | ------------------------- |
| `yt-dlp`        | **Obligatorio** (motor)    | `sudo pacman -S yt-dlp`  | `sudo apt install yt-dlp` |
| `ffmpeg`        | **Obligatorio** (fusión)   | `sudo pacman -S ffmpeg`  | `sudo apt install ffmpeg` |
| `aria2`         | Opcional (`--aria2`)       | `sudo pacman -S aria2`   | `sudo apt install aria2`  |
| `AtomicParsley` | Opcional (carátula en mp4) | `sudo pacman -S atomicparsley` | `sudo apt install atomicparsley` |
| `jq`            | Opcional (modo `info`)     | `sudo pacman -S jq`      | `sudo apt install jq`     |

> yt-dlp cambia rápido porque los sitios cambian rápido: si las descargas
> empiezan a fallar, lo primero es `./main.sh --update`.

---

## 🚀 Instalación

### 1. Dar permisos de ejecución

```bash
chmod +x ~/Documents/scripts_for_linux/script_video_downloader/main.sh
chmod +x ~/Documents/scripts_for_linux/script_video_downloader/lib/*.sh
```

### 2. Añadir alias conveniente (opcional)

```bash
# En ~/.bashrc o ~/.zshrc
alias vdl='~/Documents/scripts_for_linux/script_video_downloader/main.sh'
```

### 3. Probar en modo simulación primero

```bash
./main.sh --simulate "https://www.youtube.com/watch?v=XXXX"
```

---

## 💻 Uso

```bash
./main.sh [OPCIONES] URL [URL2 ...]
./main.sh [OPCIONES] --batch lista_urls.txt
```

### Opciones disponibles

| Flag                      | Descripción                                            | Default            |
| ------------------------- | ------------------------------------------------------ | ------------------ |
| `-h, --help`              | Ayuda completa con ejemplos                            | —                  |
| `--version`               | Versión del script                                     | —                  |
| `-v, --verbose`           | Salida detallada (incluye la de yt-dlp)                | false              |
| `-s, --simulate`          | Hace todo menos descargar (dry-run)                    | false              |
| `-l, --log`               | Log persistente con rotación                           | false              |
| `--no-confirm`            | Sin confirmación inicial (cron/scripts)                | false              |
| `--update`                | Actualiza yt-dlp y sale                                | —                  |
| `-m, --mode <m>`          | `video`·`audio`·`best`·`info`·`formats`·`subs`         | `video`            |
| `-q, --quality <q>`       | Altura máx (`2160`,`1080`,`720`…) o `best`/`worst`     | `best`             |
| `-c, --container <c>`     | `mp4`·`mkv`·`webm` al fusionar                         | `mp4`              |
| `-f, --format <str>`      | Cadena `-f` cruda de yt-dlp (ignora `--quality`)       | —                  |
| `--audio-format <f>`      | `mp3`·`m4a`·`opus`·`flac`·`wav`·`aac`·`best`           | `mp3`              |
| `--audio-quality <q>`     | `0` (mejor) … `10`, o bitrate (`192K`)                 | `0`                |
| `--clip <INI-FIN>`        | Recorta solo ese tramo, corte exacto + verificación    | —                  |
| `-o, --output-dir <dir>`  | Carpeta destino                                        | `~/Downloads/videos` |
| `-t, --template <tpl>`    | Plantilla de nombres de yt-dlp                         | ver `config.sh`    |
| `--organize`              | Subcarpetas `uploader/playlist/`                       | false              |
| `--restrict-names`        | Nombres ASCII sin espacios ni tildes                   | false              |
| `--subs` / `--auto-subs`  | Subtítulos manuales / autogenerados                    | false              |
| `--embed-subs`            | Incrustarlos en el contenedor                          | false              |
| `--sub-langs <lista>`     | Idiomas (`es,en`, `all`)                               | `es,en`            |
| `--thumbnail`             | Miniatura como carátula incrustada                     | false              |
| `--write-thumbnail`       | Miniatura como archivo aparte                          | false              |
| `--write-info`            | Volcar `.info.json` con metadatos                      | false              |
| `--no-metadata` / `--no-chapters` | Desactivar metadatos / capítulos incrustados   | (activados)        |
| `--sponsorblock`          | Recortar patrocinios/intros (SponsorBlock)             | false              |
| `--no-playlist`           | De URL de playlist, bajar solo ese video               | false              |
| `--items <sel>`           | Selección de playlist: `1:10`, `1,3,5`, `2:-1`         | —                  |
| `--max <n>`               | Tope de descargas                                      | sin límite         |
| `--archive`               | Historial persistente: no re-descargar                 | false              |
| `--retries <n>`           | Reintentos por descarga/fragmento                      | 10                 |
| `-N, --concurrent <n>`    | Fragmentos en paralelo                                 | 4                  |
| `--rate-limit <r>`        | Límite de velocidad (`2M`)                             | sin límite         |
| `--sleep <seg>`           | Espera entre videos (anti-bloqueo)                     | 0                  |
| `--aria2`                 | aria2c como descargador externo                        | false              |
| `--cookies <archivo>`     | `cookies.txt` exportado                                | —                  |
| `--cookies-browser <nav>` | Cookies del navegador (`firefox`, `chrome`, …)         | —                  |
| `--proxy <url>`           | Proxy (`socks5://…`, `http://…`)                       | —                  |
| `--user-agent <ua>`       | User-Agent personalizado                               | —                  |
| `--batch <archivo>`       | Archivo con una URL por línea (`#` = comentario)       | —                  |
| `--post-cmd <cmd>`        | Comando al finalizar (notificaciones, etc.)            | —                  |
| `--extra "<flags>"`       | Flags crudas anexadas a yt-dlp                         | —                  |

---

## 🎛️ Modos de operación

| Modo      | Qué hace                                                        |
| --------- | --------------------------------------------------------------- |
| `video`   | Mejor video+audio hasta `--quality`, fusionado a `--container`  |
| `audio`   | Solo audio, extraído a `--audio-format` (mp3 por defecto)       |
| `best`    | La mejor calidad absoluta disponible (ignora `--quality`)       |
| `info`    | Metadatos del video en JSON (resumido con `jq` si está)         |
| `formats` | Tabla de todos los formatos disponibles, sin descargar          |
| `subs`    | Solo subtítulos, sin el video                                   |

---

## 📚 Casos de uso frecuentes

```bash
# Video de YouTube a 1080p en mp4 (el caso común)
./main.sh -q 1080 "https://youtu.be/XXXX"

# Música: playlist completa a mp3, organizada en subcarpetas, sin duplicados
./main.sh -m audio --organize --archive "https://youtube.com/playlist?list=YYYY"

# Video de Facebook (privado o con login) usando cookies de Firefox
./main.sh --cookies-browser firefox "https://www.facebook.com/watch?v=ZZZZ"

# Clase/conferencia con subtítulos en español incrustados
./main.sh --subs --auto-subs --embed-subs --sub-langs "es" "https://youtu.be/XXXX"

# Los videos 3 al 7 de una playlist, máximo 720p
./main.sh -q 720 --items "3:7" "https://youtube.com/playlist?list=YYYY"

# Lote nocturno desde archivo: sin preguntas, con log y notificación
./main.sh --batch urls.txt --archive --no-confirm --log \
          --post-cmd "notify-send 'Descargas' 'Lote completado'"

# Recortar un tramo exacto (min 2:46:00 → 2:47:00) — corte al frame, A/V sincronizado
./main.sh --clip 2:46:00-2:47:00 -o ~/Downloads "https://www.facebook.com/watch?v=ZZZZ"

# Solo el audio de ese mismo tramo, en mp3
./main.sh -m audio --clip 2:46:00-2:47:00 "https://www.facebook.com/watch?v=ZZZZ"

# Ver qué formatos existen antes de decidir
./main.sh -m formats "https://youtu.be/XXXX"

# Elegir un formato exacto de esa tabla (avanzado)
./main.sh -f "137+140" "https://youtu.be/XXXX"

# Red lenta o inestable: aria2c + límite de tasa + más reintentos
./main.sh --aria2 --rate-limit 2M --retries 20 "https://youtu.be/XXXX"

# Cualquier flag de yt-dlp no envuelta, vía --extra
./main.sh --extra "--geo-bypass-country US --force-ipv4" "https://youtu.be/XXXX"
```

---

## 🗂️ Arquitectura

```
script_video_downloader/
├── main.sh              # Punto de entrada — orquesta los módulos (~120 líneas)
├── config.sh            # Configuración centralizada: TODO default editable vive aquí
├── README.md            # Esta documentación
└── lib/
    ├── logger.sh        # Logging: colores tput, niveles, rotación de log
    ├── validator.sh     # Dependencias (con degradación), destino, cookies, calidad
    ├── cli.sh           # Parseo de flags, ayuda, validación de combinaciones
    ├── options.sh       # Traduce OPT_* → array YTDLP_ARGS (el corazón del wrapper)
    ├── clipper.sh       # --clip: URLs crudas + ffmpeg + verificación ffprobe
    ├── downloader.sh    # Ejecución por objetivo, lotes, contadores éxito/fallo
    └── summary.sh       # Banner de configuración, confirmación, resumen, post-cmd
```

### Descripción de módulos

| Archivo             | Responsabilidad única                                             |
| ------------------- | ----------------------------------------------------------------- |
| `main.sh`           | Orquestación en fases numeradas (sin lógica de negocio)           |
| `config.sh`         | Defaults del usuario — el único lugar que se edita                |
| `lib/logger.sh`     | Todo el output pasa por aquí (WARN/ERROR → stderr)                |
| `lib/validator.sh`  | Falla rápido con mensaje accionable; opcionales degradan          |
| `lib/cli.sh`        | `OPT_*` desde `DEFAULT_*`, parseo, `--help`, combinaciones        |
| `lib/options.sh`    | Intención → `YTDLP_ARGS[]` (array, no string: rutas con espacios) |
| `lib/clipper.sh`    | Recorte exacto: extrae URLs, corta con ffmpeg, verifica streams   |
| `lib/downloader.sh` | Recorre objetivos; un fallo no aborta el lote                     |
| `lib/summary.sh`    | Lo que ve el usuario antes y después                              |

---

## 🔧 Solución de Problemas

| Problema                                  | Solución                                                                 |
| ----------------------------------------- | ------------------------------------------------------------------------ |
| Descargas fallan de repente en YouTube    | `./main.sh --update` (los sitios cambian; yt-dlp se actualiza seguido)   |
| Clip con imagen congelada y audio andando | Usa `--clip` (nunca `--download-sections` vía `--extra`): corta desde las URLs crudas con ffmpeg y verifica cada stream |
| `ERROR: ... Sign in to confirm`           | Usa `--cookies-browser firefox` (sesión iniciada en ese navegador)       |
| Video de Facebook/Instagram no descarga   | Casi siempre requiere cookies: `--cookies-browser <navegador>`           |
| `yt-dlp: command not found`               | `sudo apt install yt-dlp` o `pipx install yt-dlp`                        |
| Audio y video en archivos separados       | Falta `ffmpeg`: instálalo y reintenta                                    |
| Miniatura no se incrusta en mp4           | Instala `AtomicParsley`, o usa `-c mkv` (no lo necesita)                 |
| Descarga muy lenta                        | Prueba `--aria2` (multi-conexión) o sube `-N 8`                          |
| Bloqueos por demasiadas peticiones (429)  | Añade `--sleep 10` y/o `--rate-limit 1M` entre videos                    |
| Nombres con caracteres raros en NTFS/FAT  | Usa `--restrict-names`                                                   |
| `Permission denied` al ejecutar           | `chmod +x main.sh lib/*.sh`                                              |

---

## 🤝 Cómo Agregar Funcionalidades

### Para envolver una flag nueva de yt-dlp:

1. Añade el default en `config.sh` (`DEFAULT_MI_OPCION=false`).
2. En `lib/cli.sh`: inicializa `OPT_MI_OPCION="${DEFAULT_MI_OPCION}"`, añade el
   caso en `parse_args()` y documenta la flag en `show_help()`.
3. En `lib/options.sh`: anexa la traducción en la `_opts_*` temática que
   corresponda (o crea una nueva y llámala desde `build_ytdlp_args()`).
4. Actualiza la tabla de este README.

> Si solo la necesitas una vez, no la envuelvas: usa `--extra "<flag>"`.

### Estándares de código

- Máximo 30 líneas por función; prefijo `_` para funciones privadas.
- `local` para toda variable de función; toda expansión entre comillas.
- Documenta el "por qué", no el "qué".
- Los `OPT_*` se inicializan desde `DEFAULT_*` de `config.sh` — nunca
  hardcodees un default en `lib/`.
- Verifica con `bash -n` y prueba `--simulate` antes de commitear.

---

## ⚠️ Notas y Advertencias

**Uso responsable:** descarga solo contenido al que tienes derecho de acceso
(tus videos, contenido libre, o para uso personal donde la plataforma y la ley
lo permitan). Las cookies dan acceso a TU sesión: no compartas `cookies.txt`.

**`--extra` divide por espacios simples:** para flags cuyo valor contiene
espacios usa el array `EXTRA_YTDLP_OPTS` de `config.sh` (un token por
elemento), que las preserva exactamente.

**`set -e` y los patrones `[ cond ] && acción`:** las funciones de
`lib/options.sh` terminan con `return 0` explícito; sin él, un test final
falso haría retornar 1 a la función y `set -euo pipefail` abortaría el script.
Igual con contadores: se usa `var=$((var + 1))` y no `((var++))` (que devuelve
estado 1 cuando el valor previo es 0). Mantén ambos patrones al extender.

**Separadores UTF-8:** `log_separator` usa expansión `${var// /─}` y no `tr`,
porque `tr` traduce por bytes y corrompe caracteres multibyte como `─`.

**Códigos de salida:** `0` éxito · `1` fallo general (todo el lote falló) ·
`2` argumentos inválidos · `3` archivo no encontrado · `4` sin permisos ·
`5` dependencia faltante. El código `101` de yt-dlp (tope `--max` alcanzado)
se trata como éxito.

**Playlists grandes:** yt-dlp reanuda con `--continue` y `--no-overwrites`
(activados siempre); con `--archive` además nunca re-descarga lo ya bajado,
ideal para sincronizar canales periódicamente vía cron.

**Por qué `--clip` no usa `--download-sections`:** el descargador de secciones
de yt-dlp puede truncar el stream de video en sitios DASH (Facebook sirve
video y audio por separado): el resultado es un clip con audio completo pero
imagen congelada a mitad. `lib/clipper.sh` evita ese componente: extrae las
URLs crudas del CDN (`yt-dlp -g`), corta con ffmpeg usando búsqueda de entrada
(`-ss` antes de `-i`: salta por rangos HTTP al keyframe previo, decodifica y
descarta hasta el punto exacto) y re-codifica el tramo (x264 CRF 20, ajustable
en `config.sh`) — cada frame queda decodificable y la sincronía es exacta.
Al final **verifica con ffprobe** que cada stream dure lo pedido: un clip
truncado se reporta como fallo, nunca se entrega en silencio. `--clip` opera
sobre videos individuales (aplica `--no-playlist` internamente).

**Nombre del clip cuando el sitio no da título:** algunos videos (Facebook en
particular) devuelven un título vacío o un simple `.`; con la plantilla
`<título> [<id>]` eso generaría un archivo **oculto** (`. [id] (clip …).mp4`,
que empieza por `.`). `lib/clipper.sh` recorta los puntos/espacios iniciales y
conserva el `[id]`; si no queda nada imprimible usa `CLIP_FALLBACK_PREFIX`
(`config.sh`) con marca de tiempo. Así el clip siempre queda visible y con un
nombre útil.

---

_video-downloader v1.1.1 — Compatible con Kubuntu y Arch Linux_
_achalmaedison — motor: yt-dlp + ffmpeg_
