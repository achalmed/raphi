"""CLI argument parsing for whisper-transcriber.

Defines every flag in one place; main.py only consumes the parsed
namespace. Help texts are in Spanish (user-facing), following the
project convention.
"""
from __future__ import annotations

import argparse

import config

_EPILOG = """\
Ejemplos:
  # Transcribir un audio local (autodetección de idioma)
  python3 main.py entrevista.mp3

  # Video de YouTube, idioma fijado y modelo ligero para CPU
  python3 main.py "https://youtu.be/XXXXXXX" --language es --model small

  # Traducir al inglés (salidas con sufijo .en) y acortar subtítulos
  python3 main.py charla.wav --task translate --shorten-srt

  # Solo reformatear un subtítulo existente a líneas de 42 caracteres
  python3 main.py pelicula.srt --max-line-length 42

  # Simulación: ver el plan completo sin descargar ni transcribir nada
  python3 main.py entrevista.mp3 --dry-run
"""


def positive_int(raw: str) -> int:
    """argparse type: strictly positive integer (for --max-line-length)."""
    try:
        value = int(raw)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{raw}' no es un número entero")
    if value < 1:
        raise argparse.ArgumentTypeError("debe ser un entero positivo")
    return value


def build_argument_parser() -> argparse.ArgumentParser:
    """Builds the full parser: inputs + transcription/subtitle/general flags."""
    parser = argparse.ArgumentParser(
        prog=config.APP_NAME,
        description=("Transcribe y traduce audio/video con OpenAI Whisper, "
                     "desde archivos locales o URLs (YouTube y otros sitios "
                     "compatibles con yt-dlp)."),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # re-declared below so the help text is in Spanish
    )
    parser.add_argument(
        "inputs", nargs="*", metavar="ENTRADA",
        help=("archivo de audio/video, URL de YouTube, o subtítulo .srt "
              "(los .srt solo se acortan, no se transcriben)"))

    whisper_group = parser.add_argument_group("Transcripción")
    whisper_group.add_argument(
        "-t", "--task", choices=config.AVAILABLE_TASKS,
        default=config.DEFAULT_TASK,
        help=("tarea de Whisper: transcribe o translate — traducir siempre "
              "produce inglés (por defecto: %(default)s)"))
    whisper_group.add_argument(
        "-m", "--model", choices=config.AVAILABLE_MODELS,
        default=config.DEFAULT_MODEL, metavar="MODELO",
        help=("modelo de Whisper: tiny, base, small, medium, large, turbo... "
              "(por defecto: %(default)s; en CPU se recomienda small o turbo)"))
    whisper_group.add_argument(
        "-l", "--language", metavar="CODIGO", default=None,
        help=("código del idioma del audio (es, en, fr...); sin esta opción "
              "Whisper lo autodetecta"))
    whisper_group.add_argument(
        "--list-languages", action="store_true",
        help="muestra los códigos de idioma soportados y sale")
    whisper_group.add_argument(
        "-o", "--output-dir", default=config.DEFAULT_OUTPUT_DIR, metavar="DIR",
        help="directorio donde escribir las salidas (por defecto: %(default)s)")
    whisper_group.add_argument(
        "-f", "--output-format", choices=config.OUTPUT_FORMATS,
        default=config.DEFAULT_OUTPUT_FORMAT, metavar="FORMATO",
        help=("formato de salida: txt, vtt, srt, tsv, json o all "
              "(por defecto: %(default)s)"))

    srt_group = parser.add_argument_group("Subtítulos")
    srt_group.add_argument(
        "--shorten-srt", action="store_true",
        help=("reformatea los .srt generados a líneas cortas conservando "
              "todo el texto"))
    srt_group.add_argument(
        "--max-line-length", type=positive_int,
        default=config.DEFAULT_MAX_LINE_LENGTH, metavar="N",
        help=("longitud máxima de línea al acortar subtítulos "
              "(por defecto: %(default)s, recomendación BBC)"))

    general_group = parser.add_argument_group("Generales")
    general_group.add_argument(
        "--keep-audio", action="store_true",
        help=("conserva junto a las salidas el audio descargado de URLs "
              "(por defecto se borra al terminar)"))
    general_group.add_argument(
        "-d", "--dry-run", action="store_true",
        help="simula: muestra qué se haría sin descargar ni escribir nada")
    general_group.add_argument(
        "-v", "--verbose", action="store_true",
        help="salida detallada (nivel DEBUG)")
    general_group.add_argument(
        "--version", action="version",
        version=f"{config.APP_NAME} {config.VERSION}",
        help="muestra la versión y sale")
    general_group.add_argument(
        "-h", "--help", action="help",
        help="muestra esta ayuda y sale")
    return parser
