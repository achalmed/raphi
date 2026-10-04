---
tipo: readme
estado: activo
---
# script_audio_converter/ — notas de voz de WhatsApp (Opus) y otros audios a MP3 por lotes con ffmpeg
<!-- suite:inicio -->
**Suite `audio_converter`** · objetivo *multimedia* · estado *activo* · python · interfaz cli

Convierte por lotes audios de WhatsApp (Opus) y otros formatos a MP3 con ffmpeg.

- Escribe en: archivos · simula por defecto: no
- Depende de: ffmpeg

Comandos:

```bash
main.py <carpeta> [--dry-run]
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-09-20); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

Convierte a `.mp3` un archivo de audio suelto o carpetas enteras (las notas de voz de WhatsApp, `.opus` en
contenedor OGG, y cualquier formato que ffmpeg decodifique). Es la pieza local de la cadena de audio:
[`script_video_downloader`](../script_video_downloader/) baja de una URL, esta herramienta convierte archivos que ya
están en disco y [`script_whisper_transcriber`](../script_whisper_transcriber/) transcribe el `.mp3`.

- **Qué escribe:** un `.mp3` por origen, junto a cada archivo o en el directorio de `--output-dir` (que crea si no
  existe). MP3 CBR con `libmp3lame`, conservando las etiquetas del original (`-map_metadata 0`, ID3v2.3).
- **Qué no toca:** los archivos de origen nunca se modifican ni se borran. No escribe log en disco (`LOG_FILE = None`
  en `config.py`); los mensajes van a la terminal.
- **Qué no hace:** no descarga de la red ni produce otro formato que MP3.
- **Simulación:** no simula por defecto; `-d`/`--dry-run` muestra el plan sin escribir nada y, sin ffmpeg instalado,
  solo avisa en lugar de abortar.
- **Idempotente:** si el `.mp3` de destino ya existe, lo omite salvo `--overwrite`.

## Uso

```bash
python3 main.py PTT-20260730-WA0001.opus                       # el .mp3 queda junto al .opus
python3 main.py ~/WhatsApp/"WhatsApp Voice Notes" -r -o ~/Audios_mp3   # carpeta con subcarpetas
python3 main.py nota.opus audios_sueltos/ --bitrate 192k       # entradas mezcladas
python3 main.py ~/Audios_wa -r --dry-run                       # simula: nada se escribe
python3 main.py nota.opus -o /tmp/mp3 && \
    python3 ../script_whisper_transcriber/main.py /tmp/mp3/nota.mp3 --model small
```

`ENTRADA` (una o varias) es un archivo o una carpeta. Al escanear carpetas solo se recogen las extensiones de
`AUDIO_EXTENSIONS` (`.opus .ogg .oga .m4a .aac .amr .wav .flac .wma`); un archivo nombrado en la línea de órdenes se
intenta con cualquier extensión (ffmpeg decide), salvo un `.mp3`, que se omite.

| opción | qué hace | por defecto (`config.py`) |
|---|---|---|
| `ENTRADA ...` | archivos o carpetas de audio | obligatorio |
| `-o`, `--output-dir DIR` | directorio de los `.mp3` | junto a cada origen |
| `-r`, `--recursive` | busca también en subcarpetas | no (`DEFAULT_RECURSIVE = False`) |
| `-b`, `--bitrate TASA` | bitrate CBR en la forma `128k`, entre 32k y 320k | `128k` (`DEFAULT_BITRATE`) |
| `--overwrite` | reconvierte aunque el `.mp3` exista | no |
| `-d`, `--dry-run` | simula | no |
| `-v`, `--verbose` | nivel DEBUG: muestra la orden de ffmpeg de cada archivo | no |
| `--version` | imprime la versión | — |
| `-h`, `--help` | ayuda con ejemplos | — |

Códigos de salida: 0 éxito o nada que convertir · 1 alguna conversión falló · 2 uso (bitrate inválido, salida que
no es directorio) · 3 ruta inexistente · 4 sin permisos · 5 falta ffmpeg · 130 interrumpido.

Requisitos: Python 3 (solo biblioteca estándar) y `ffmpeg` con `libmp3lame`. El logger es el común del
espacio de trabajo (carpeta core, py-common), que `lib/logger.py` busca subiendo desde su carpeta.

## Estructura

| archivo | qué hace |
|---|---|
| `main.py` | orquesta: argumentos → logger → validación → descubrir y planificar → convertir → resumen |
| `config.py` | extensiones, bitrate por defecto y límites, argumentos de ffmpeg, colores, códigos de salida, `LOG_FILE` |
| `lib/__init__.py` | marca `lib/` como paquete |
| `lib/cli.py` | parser `argparse` con la ayuda y los ejemplos en español |
| `lib/logger.py` | envoltorio del logger común (carpeta core del espacio de trabajo, py-common) |
| `lib/validator.py` | comprueba ffmpeg, entradas, permisos, bitrate y crea el directorio de salida |
| `lib/scanner.py` | expande carpetas por extensión, deduplica orígenes y descarta destinos repetidos |
| `lib/converter.py` | ejecuta ffmpeg sin shell para un archivo; borra el `.mp3` si la conversión falla o queda vacío |

## Límite honesto

- **Solo produce MP3**: no existe una opción de formato.
- **`--output-dir` aplana**: con `-r -o DIR` todos los `.mp3` caen en `DIR`, sin recrear las subcarpetas. Dos orígenes
  con el mismo nombre base (`a.opus`, `a.ogg`) apuntan al mismo `a.mp3`: se convierte el primero y el resto se omite
  con aviso. Sin `-o` cada salida queda junto a su origen y no hay choque.
- **El error de ffmpeg se resume en una línea**: ante un fallo se imprime la última línea de su salida de error,
  con o sin `-v`; `-v` añade la orden ejecutada, no más detalle del error. Para verlo entero, repetir esa orden a mano.
- **Una entrada inexistente o ilegible aborta todo el lote** antes de convertir nada.
- **«Ya existe» se decide por el nombre**, no por el contenido: un `.mp3` previo incompleto o de otra fuente se omite
  igual; `--overwrite` lo rehace.
- Pensada para Linux; en macOS debería funcionar con ffmpeg, pero no está probada; en Windows, tampoco.
