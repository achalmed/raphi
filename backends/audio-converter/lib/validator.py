"""Input, option and dependency validation for audio-converter.

Everything is checked before any conversion starts so failures happen
early, with actionable Spanish messages and the project's exit codes.
In --dry-run mode a missing ffmpeg degrades to a warning so the plan can
still be inspected.
"""
from __future__ import annotations

import os
import re
import shutil
import sys
from logging import Logger
from pathlib import Path
from typing import List, Optional

import config

_BITRATE_PATTERN = re.compile(r"^(\d+)k$")


def validate_dependencies(dry_run: bool, logger: Logger) -> None:
    """ffmpeg is the only external requirement."""
    if shutil.which("ffmpeg") is not None:
        return
    message = ("Falta la dependencia 'ffmpeg' "
               "(instálala con: sudo apt install ffmpeg).")
    if dry_run:
        logger.warning(message)
        logger.warning("Simulación: se continúa aunque falte ffmpeg.")
    else:
        logger.error(message)
        sys.exit(config.EXIT_DEPENDENCY)


def validate_inputs(raw_inputs: List[str], logger: Logger) -> List[Path]:
    """Verifies every input path (file or directory) exists and is readable.

    Exits on the first invalid input: a partial batch is worse than a
    clear early failure.
    """
    validated = []
    for raw in raw_inputs:
        path = Path(raw).expanduser()
        if not path.exists():
            logger.error("La ruta '%s' no existe.", path)
            sys.exit(config.EXIT_NOT_FOUND)
        if not os.access(path, os.R_OK):
            logger.error("Sin permisos para leer '%s'.", path)
            sys.exit(config.EXIT_PERMISSION)
        validated.append(path)
    return validated


def validate_bitrate(raw: str, logger: Logger) -> str:
    """Accepts LAME CBR bitrates in the '128k' form, within sane MP3 limits."""
    match = _BITRATE_PATTERN.match(raw)
    if match is None:
        logger.error("Bitrate inválido: '%s'. Usa la forma '128k' "
                     "(ej.: 96k, 128k, 192k).", raw)
        sys.exit(config.EXIT_USAGE)
    kbps = int(match.group(1))
    if not config.MIN_BITRATE_KBPS <= kbps <= config.MAX_BITRATE_KBPS:
        logger.error("Bitrate fuera de rango: '%s' (MP3 admite %d-%d kbps).",
                     raw, config.MIN_BITRATE_KBPS, config.MAX_BITRATE_KBPS)
        sys.exit(config.EXIT_USAGE)
    return raw


def validate_output_dir(raw: Optional[str], dry_run: bool,
                        logger: Logger) -> Optional[Path]:
    """Ensures the output directory exists (creating it) and is writable.

    Returns None when the user did not request one (outputs are then
    written next to each source file).
    """
    if raw is None:
        return None
    out_dir = Path(raw).expanduser()
    if out_dir.exists():
        if not out_dir.is_dir():
            logger.error("'%s' existe y no es un directorio.", out_dir)
            sys.exit(config.EXIT_USAGE)
        if not os.access(out_dir, os.W_OK):
            logger.error("Sin permisos de escritura en '%s'.", out_dir)
            sys.exit(config.EXIT_PERMISSION)
        return out_dir
    if dry_run:
        logger.info("[SIMULACIÓN] Se crearía el directorio de salida '%s'.",
                    out_dir)
        return out_dir
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        logger.error("Sin permisos para crear el directorio '%s'.", out_dir)
        sys.exit(config.EXIT_PERMISSION)
    return out_dir
