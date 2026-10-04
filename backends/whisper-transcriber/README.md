---
tipo: readme
estado: activo
---
# script_whisper_transcriber/ — transcripción y traducción local de audio o video con Whisper, con subtítulos
<!-- suite:inicio -->
**Suite `whisper_transcriber`** · objetivo *multimedia* · estado *activo* · python · interfaz cli

Transcribe y traduce audio o video localmente con Whisper.

- Escribe en: archivos · simula por defecto: no
- Depende de: whisper, ffmpeg, yt-dlp (solo para URL), pysrt (opcional)

Comandos:

```bash
main.py <archivo> [--language es] [--dry-run]
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-10-04); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

Ejecuta en la máquina el CLI `whisper` (OpenAI Whisper) sobre audio o video y deja la transcripción en `txt`, `srt`,
`vtt`, `tsv` y `json`. Cada entrada se clasifica sola:

- **Archivo de audio o video** (lo que ffmpeg decodifique) → transcripción, o traducción al inglés con
  `--task translate`.
- **URL `http://` o `https://`** → baja el audio en mp3 con `yt-dlp` (solo ese video, nunca la lista entera) y lo
  transcribe.
- **Archivo `.srt`** → no se transcribe: se reparte el texto en líneas de como mucho `--max-line-length` caracteres,
  por palabras y sin perder texto.

Es el último eslabón de la cadena de audio: [`script_video_downloader`](../script_video_downloader/) baja de la red
y [`script_audio_converter`](../script_audio_converter/) convierte a mp3 lo que ya está en disco.

- **Qué escribe:** en `--output-dir` (por defecto, la carpeta actual) `<nombre>.<formato>` por cada formato pedido;
  Whisper sobrescribe lo que ya exista. Con `--task translate` las salidas se llaman `<nombre>.en.<formato>`, así que
  no pisan la transcripción. El acortado se escribe como `<nombre>_acortado.srt` junto al `.srt` de origen, sin tocar
  el original. Con `--keep-audio`, el mp3 bajado de una URL queda en `--output-dir`; si no, se borra con su carpeta
  temporal. Los archivos de entrada nunca se modifican. No escribe log en disco.
- **Simulación:** no simula por defecto; `-d`/`--dry-run` muestra el plan sin descargar, transcribir ni escribir, y
  convierte en avisos las dependencias que falten.

## Uso

```bash
python3 main.py entrevista.mp3 --language es                       # transcribe; todos los formatos
python3 main.py "https://youtu.be/XXXX" --language es --model small
python3 main.py charla.wav --task translate --shorten-srt          # al inglés, con .srt acortado
python3 main.py pelicula.srt --max-line-length 42                  # solo acorta
python3 main.py entrevista.mp3 "https://youtu.be/XXXX" --dry-run
python3 main.py --list-languages
```

Varias entradas se procesan en orden; el fallo de una no detiene a las demás.

| opción | qué hace | por defecto (`config.py`) |
|---|---|---|
| `ENTRADA ...` | archivos, URL o `.srt` | obligatoria salvo con `--list-languages` |
| `-t`, `--task` | `transcribe` o `translate` (siempre al inglés) | `transcribe` |
| `-m`, `--model MODELO` | `tiny`, `base`, `small`, `medium`, `large` (y sus variantes `.en`, `-v1`…`-v3`), `turbo`, `large-v3-turbo` | `large` (`DEFAULT_MODEL`) |
| `-l`, `--language CODIGO` | idioma del audio; se valida contra el catálogo | autodetección de Whisper |
| `--list-languages` | lista los códigos admitidos y sale | — |
| `-o`, `--output-dir DIR` | carpeta de salida; la crea si falta | `.` |
| `-f`, `--output-format F` | `txt`, `vtt`, `srt`, `tsv`, `json` o `all` | `all` |
| `--shorten-srt` | acorta también los `.srt` generados | no |
| `--max-line-length N` | longitud máxima de línea al acortar | `37` |
| `--keep-audio` | conserva el mp3 descargado | no |
| `-d`, `--dry-run` | simula | no |
| `-v`, `--verbose` | nivel DEBUG | no |
| `--version` | imprime la versión | — |
| `-h`, `--help` | ayuda con ejemplos | — |

Códigos de salida: 0 todo bien · 1 alguna entrada falló · 2 argumentos o idioma inválido · 3 archivo inexistente ·
4 sin permisos · 5 falta una dependencia · 130 interrumpido.

Requisitos (`requirements.txt` y sistema): `openai-whisper` (el CLI `whisper`) y `ffmpeg`, siempre que haya algo que
transcribir; `yt-dlp` solo con URL; `pysrt` solo para acortar. El validador exige únicamente lo que la ejecución
concreta necesita.

## Estructura

| archivo | qué hace |
|---|---|
| `main.py` | orquesta: argumentos → validación → por entrada (URL → descarga; medio → Whisper; `.srt` → acortado) → resumen; borra la carpeta temporal al final |
| `config.py` | modelo, tarea y formato por defecto, etiqueta de traducción, plantilla de yt-dlp, longitud de línea, catálogo de idiomas, códigos de salida |
| `requirements.txt` | paquetes de Python |
| `lib/__init__.py` | marca `lib/` como paquete |
| `lib/cli.py` | parser `argparse` con ejemplos |
| `lib/logger.py` | envoltorio del logger común (carpeta core del espacio de trabajo, py-common) |
| `lib/validator.py` | clasifica entradas, comprueba idioma, permisos, dependencias necesarias y carpeta de salida |
| `lib/downloader.py` | `yt-dlp` sin shell: audio en mp3, nombre seguro, sin listas; mueve el mp3 con `--keep-audio` |
| `lib/transcriber.py` | ejecuta `whisper`; en traducción escribe en una carpeta temporal y mueve las salidas con la etiqueta `.en` |
| `lib/subtitle_shortener.py` | reparte el texto de cada subtítulo en líneas cortas y guarda el `_acortado.srt` |

## Límite honesto

- **`large` por defecto es muy lento en CPU**: está pensado para GPU. En CPU, `--model small` o `turbo`, o cambiar
  `DEFAULT_MODEL`. El aviso de Whisper «FP16 is not supported on CPU» es informativo.
- **`--task translate` solo produce inglés** (límite de Whisper).
- **La transcripción se revisa a mano**: cifras, nombres propios y siglas son donde más se equivoca.
- **No baja el video completo**, solo el audio que necesita; para el video, `script_video_downloader`.
- **`--shorten-srt` no hace nada si no se genera `.srt`** (con `-f txt`, por ejemplo): avisa y sigue.
- **Las descargas de YouTube fallan cuando el sitio cambia**: se actualiza `yt-dlp`.
- Probada en Linux; en macOS debería funcionar con los mismos binarios, sin probar.
- Deriva del cuaderno de Colab «Transcribir y Traducir OpenAI Whisper» de Jason Boog, publicado con licencia MIT; esa
  licencia se conserva para el código derivado.
