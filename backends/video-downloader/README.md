---
tipo: readme
estado: activo
---
# script_video_downloader/ — descarga de video o audio con yt-dlp y ffmpeg, por URL o por lotes, con recorte exacto
<!-- suite:inicio -->
**Suite `video_downloader`** · objetivo *multimedia* · estado *activo* · bash · interfaz cli

Descarga video o audio con yt-dlp y ffmpeg, por URL o por lotes, con recorte opcional.

- Escribe en: archivos · simula por defecto: no
- Depende de: yt-dlp, ffmpeg

Comandos:

```bash
main.sh <url>
main.sh -m audio --audio-format mp3 <url>
main.sh --batch lista.txt
main.sh --simulate <url>
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-10-03); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

Envoltorio de `yt-dlp` con opciones en español y valores por defecto en `config.sh`: video hasta una altura máxima,
solo audio, subtítulos, listas de reproducción, lotes desde un archivo, historial para no repetir descargas,
SponsorBlock y recorte exacto de un tramo (`--clip`). Lo que no envuelve llega a yt-dlp con `--extra` o con el
arreglo `EXTRA_YTDLP_OPTS` de `config.sh`. Es la pieza de red de la cadena de audio: lo que baja en mp3 lo
transcribe [`script_whisper_transcriber`](../script_whisper_transcriber/); los audios que ya están en disco los
convierte [`script_audio_converter`](../script_audio_converter/).

Modos (`-m`): `video` (mejor video y audio hasta `-q`, fusionados en `-c`), `audio` (extrae a `--audio-format`),
`best` (la mejor calidad, sin tope), `info` (metadatos en JSON, resumidos con `jq` si está), `formats` (tabla de
formatos, sin descargar) y `subs` (solo subtítulos).

- **Qué escribe:** en `--output-dir` (por defecto «~/Downloads/videos», que crea si falta) con la plantilla
  `%(title)s [%(id)s].%(ext)s`, o `uploader/lista/título [id]` con `--organize`; siempre con `--continue` y
  `--no-overwrites`. Con `--archive`, el historial en «~/.local/share/video_downloader/descargados.txt». Con
  `-l`/`--log`, «~/video_downloader.log» (se archiva al pasar de 10 MB). Un clip se guarda como
  `<título> [<id>] (clip <rango>).<ext>`.
- **Simulación:** no simula por defecto; `-s`/`--simulate` pasa `--simulate` a yt-dlp y no descarga ni recorta (sí
  consulta la red). Tampoco pide confirmación en simulación ni en los modos `info` y `formats`.

## Uso

```bash
./main.sh --simulate "https://youtu.be/XXXX"                       # simula
./main.sh -q 1080 "https://youtu.be/XXXX"                          # video a 1080p en mp4
./main.sh -m audio --audio-format mp3 "https://youtu.be/XXXX"      # solo audio
./main.sh -m audio --organize --archive "https://youtube.com/playlist?list=YYYY"
./main.sh --cookies-browser firefox "https://www.facebook.com/watch?v=ZZZZ"
./main.sh --subs --auto-subs --embed-subs --sub-langs es "https://youtu.be/XXXX"
./main.sh --clip 2:46:00-2:47:00 -o ~/Downloads "https://www.facebook.com/watch?v=ZZZZ"
./main.sh --batch urls.txt --archive --no-confirm --log
./main.sh -m formats "https://youtu.be/XXXX"; ./main.sh -f "137+140" "https://youtu.be/XXXX"
./main.sh --update                                                 # yt-dlp -U y sale
```

En `--batch`, una URL por línea; las vacías y las que empiezan por `#` se saltan. Un fallo no detiene el lote.

| opción | qué hace | por defecto (`config.sh`) |
|---|---|---|
| `-h`, `--help` / `--version` | ayuda con ejemplos / versión | — |
| `-v`, `--verbose` | detalle, incluida la salida de yt-dlp | `false` |
| `-s`, `--simulate` | simula | `false` |
| `-l`, `--log` | log en «~/video_downloader.log» | `false` |
| `--no-confirm` | no pide confirmación | `false` |
| `--update` | ejecuta `yt-dlp -U` y sale | — |
| `-m`, `--mode M` | `video`, `audio`, `best`, `info`, `formats`, `subs` | `video` |
| `-q`, `--quality Q` | altura máxima (`2160`, `1080`, `720`…), `best` o `worst` | `best` |
| `-c`, `--container C` | `mp4`, `mkv` o `webm` al fusionar | `mp4` |
| `-f`, `--format STR` | cadena `-f` cruda de yt-dlp (ignora `-q`) | — |
| `--audio-format F` | `mp3`, `m4a`, `opus`, `flac`, `wav`, `vorbis`, `aac` o `best` | `mp3` |
| `--audio-quality Q` | `0` (mejor) a `10`, o un bitrate (`192K`) | `0` |
| `--clip INI-FIN` | recorta ese tramo (`H:MM:SS`, `MM:SS` o segundos); solo modos `video`, `best`, `audio` | — |
| `-o`, `--output-dir DIR` | carpeta de destino | «~/Downloads/videos» |
| `-t`, `--template TPL` | plantilla de nombres de yt-dlp | `%(title)s [%(id)s].%(ext)s` |
| `--organize` | subcarpetas por autor y lista | `false` |
| `--restrict-names` | nombres ASCII sin espacios | `false` |
| `--subs` / `--auto-subs` | subtítulos manuales / automáticos (en `srt`) | `false` |
| `--embed-subs` | los incrusta (implica `--subs`) | `false` |
| `--sub-langs LISTA` | idiomas (`es,en`, `all`) | `es,en` |
| `--thumbnail` / `--write-thumbnail` | miniatura incrustada / como archivo | `false` |
| `--write-info` | guarda el `.info.json` | `false` |
| `--no-metadata` / `--no-chapters` | no incrusta metadatos / capítulos | se incrustan |
| `--sponsorblock` | quita `sponsor,selfpromo,interaction` | `false` |
| `--no-playlist` | de una URL de lista, solo ese video | `false` |
| `--items SEL` | selección de la lista (`1:10`, `1,3,5`, `2:-1`) | — |
| `--max N` | tope de descargas | `0` (sin tope) |
| `--archive` | historial: no repite lo ya bajado | `false` |
| `--retries N` | reintentos | `10` |
| `-N`, `--concurrent N` | fragmentos en paralelo | `4` |
| `--rate-limit R` | límite de velocidad (`2M`) | sin límite |
| `--sleep S` | segundos entre videos | `0` |
| `--aria2` | usa `aria2c` como descargador | `false` |
| `--cookies ARCHIVO` / `--cookies-browser NAV` | cookies de un archivo / del navegador (excluyentes) | — |
| `--proxy URL` / `--user-agent UA` | proxy / User-Agent | — |
| `--batch ARCHIVO` | lista de URL | — |
| `--post-cmd CMD` | ejecuta `CMD` con `bash -c` al terminar (no en simulación) | — |
| `--extra "FLAGS"` | opciones crudas para yt-dlp, separadas por espacios | — |

Códigos de salida: 0 éxito (el 101 de yt-dlp por `--max` cuenta como éxito) · 1 todos los objetivos fallaron o no
se pudo crear la carpeta · 2 argumentos · 3 archivo de lote o de cookies inexistente · 4 sin permisos · 5 falta una
dependencia.

Requisitos: Bash ≥ 4.3, `yt-dlp`, `ffmpeg` y `ffprobe`; opcionales `aria2c` (`--aria2`), `AtomicParsley` (carátula
en mp4) y `jq` (resumen del modo `info`).

## Estructura

| archivo | qué hace |
|---|---|
| `main.sh` | orquesta: argumentos → logger → `--update` → validación → objetivos → argumentos de yt-dlp → confirmación → descarga → resumen → `--post-cmd` |
| `config.sh` | valores por defecto, plantillas de nombre, historial, parámetros del clip, red, cookies, log |
| `lib/cli.sh` | parser de opciones, ayuda, versión y combinaciones inválidas |
| `lib/logger.sh` | envoltorio del logger común (carpeta core del espacio de trabajo, shell-lib); abre el log solo con `--log` |
| `lib/validator.sh` | dependencias, calidad, cookies, carpeta de destino, objetivos |
| `lib/options.sh` | traduce las opciones al arreglo de argumentos de yt-dlp |
| `lib/clipper.sh` | `--clip`: URL crudas con `yt-dlp -g`, corte con ffmpeg, verificación con ffprobe, nombre del clip |
| `lib/downloader.sh` | lotes, un objetivo por modo, contadores de éxito y fallo |
| `lib/summary.sh` | banner de configuración, confirmación, resumen y `--post-cmd` |

## Límite honesto

- **Solo lo que se tiene derecho a descargar**: las cookies dan acceso a la sesión del navegador; `cookies.txt` no se
  comparte.
- **Los sitios cambian**: si las descargas empiezan a fallar, lo primero es `./main.sh --update` (si yt-dlp vino del
  gestor de paquetes y `-U` falla, se actualiza por ese gestor). Facebook e Instagram casi siempre piden
  cookies.
- **`--clip` re-codifica el tramo** (x264 CRF 20, preset `veryfast`, AAC 128k; ajustables en `config.sh`), solo
  opera sobre videos individuales y verifica con ffprobe que cada stream dure lo pedido: un clip truncado cuenta como
  fallo, aunque el archivo queda en disco (solo se borra si falla ffmpeg). No se debe sustituir por `--download-sections` vía `--extra`: en sitios DASH
  trunca el video y deja la imagen congelada.
- **`--clip` en modo audio con `vorbis` o `best`** codifica AAC, pero la extensión del archivo es la palabra pedida.
- **`--extra` divide por espacios simples**: un valor con espacios va en `EXTRA_YTDLP_OPTS` de `config.sh`, un
  elemento por token.
- **`--simulate` no es del todo inocuo**: con `--archive` crea la carpeta del historial (ver `docs/decisiones.md`
  §Pendientes) y siempre consulta la red.
- **`--post-cmd` ejecuta el texto tal cual** con `bash -c`.
- **Subtítulos siempre en `srt`** (`DEFAULT_SUB_FORMAT`); no hay opción para cambiarlo.
- **Miniatura incrustada en mp4** necesita `AtomicParsley`; con `-c mkv` no.
- Escrito para Linux; sin probar en macOS.
