"""CLI argument parsing for audio-converter.

Defines every flag in one place; main.py only consumes the parsed
namespace. Help texts are in Spanish (user-facing), following the
project convention.
"""
from __future__ import annotations

import argparse

import config

_EPILOG = """\
Ejemplos:
  # Convertir una nota de voz suelta (el .mp3 queda junto al .opus)
  python3 main.py PTT-20260730-WA0001.opus

  # Toda la carpeta de notas de voz de WhatsApp (subcarpetas por semana)
  python3 main.py ~/WhatsApp/"WhatsApp Voice Notes" -r -o ~/Audios_mp3

  # Varias entradas mezcladas, con más calidad
  python3 main.py nota.opus audios_sueltos/ --bitrate 192k

  # Repetir una carpeta: lo ya convertido se omite (usa --overwrite para rehacer)
  python3 main.py ~/Audios_wa -o ~/Audios_mp3

  # Simulación: ver qué se convertiría sin escribir nada
  python3 main.py ~/Audios_wa -r --dry-run

Encadenar con el transcriptor:
  python3 main.py nota.opus -o /tmp/mp3 && \\
      python3 ../script_whisper_transcriber/main.py /tmp/mp3/nota.mp3 --model small
"""


def build_argument_parser() -> argparse.ArgumentParser:
    """Builds the full parser: inputs + conversion/general flags."""
    parser = argparse.ArgumentParser(
        prog=config.APP_NAME,
        description=("Convierte audios de WhatsApp (.opus, .ogg, .m4a...) — "
                     "y cualquier audio que ffmpeg entienda — a .mp3, por "
                     "lotes. Complementa a script_video_downloader (URLs) y "
                     "a script_whisper_transcriber (transcripción)."),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # re-declared below so the help text is in Spanish
    )
    parser.add_argument(
        "inputs", nargs="+", metavar="ENTRADA",
        help=("archivo de audio o carpeta con audios; las carpetas se "
              "filtran por extensión (%s)" % ", ".join(config.AUDIO_EXTENSIONS)))

    conversion_group = parser.add_argument_group("Conversión")
    conversion_group.add_argument(
        "-o", "--output-dir", default=None, metavar="DIR",
        help=("directorio donde dejar los .mp3 (por defecto, junto a cada "
              "archivo de origen)"))
    conversion_group.add_argument(
        "-r", "--recursive", action="store_true",
        default=config.DEFAULT_RECURSIVE,
        help=("busca audios también en subcarpetas (WhatsApp guarda las "
              "notas de voz en subcarpetas por semana)"))
    conversion_group.add_argument(
        "-b", "--bitrate", default=config.DEFAULT_BITRATE, metavar="TASA",
        help="bitrate del mp3, forma '128k' (por defecto: %(default)s)")
    conversion_group.add_argument(
        "--overwrite", action="store_true",
        help="reconvierte aunque el .mp3 de destino ya exista")

    general_group = parser.add_argument_group("Generales")
    general_group.add_argument(
        "-d", "--dry-run", action="store_true",
        help="simula: muestra qué se convertiría sin escribir nada")
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
