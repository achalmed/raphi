"""Input, option and dependency validation for whisper-transcriber.

Everything is checked before any work starts so failures happen early,
with actionable Spanish messages and the project's exit codes. In
--dry-run mode missing dependencies degrade to warnings so the plan can
be inspected on machines that do not have Whisper installed yet.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from logging import Logger
from pathlib import Path
from typing import List, Tuple, Union

import config

InputItem = Tuple[str, Union[str, Path]]  # (kind, url-or-path)

_INSTALL_HINTS = {
    "whisper": "pip install -U openai-whisper",
    "ffmpeg": "sudo apt install ffmpeg",
    "yt-dlp": "pip install -U yt-dlp",
    "pysrt": "pip install pysrt",
}


def classify_input(raw: str) -> InputItem:
    """Classifies one CLI input as 'url', 'srt' or 'media' (audio/video)."""
    if raw.lower().startswith(config.URL_PREFIXES):
        return ("url", raw)
    path = Path(raw).expanduser()
    kind = "srt" if path.suffix.lower() == ".srt" else "media"
    return (kind, path)


def validate_inputs(raw_inputs: List[str], logger: Logger) -> List[InputItem]:
    """Classifies every input and verifies local files exist and are readable.

    Exits with EXIT_NOT_FOUND / EXIT_PERMISSION / EXIT_USAGE on the first
    invalid input: a partial batch is worse than a clear early failure.
    """
    classified = []
    for raw in raw_inputs:
        kind, item = classify_input(raw)
        if kind != "url":
            if not item.exists():
                logger.error("El archivo '%s' no existe.", item)
                sys.exit(config.EXIT_NOT_FOUND)
            if item.is_dir():
                logger.error(
                    "'%s' es un directorio; se esperaba un archivo o una URL.",
                    item)
                sys.exit(config.EXIT_USAGE)
            if not os.access(item, os.R_OK):
                logger.error("Sin permisos para leer '%s'.", item)
                sys.exit(config.EXIT_PERMISSION)
        classified.append((kind, item))
    return classified


def validate_language(code: str | None, logger: Logger) -> None:
    """Rejects unknown language codes with a hint instead of a Whisper crash."""
    if code is None or code in config.SUPPORTED_LANGUAGES:
        return
    logger.error(
        "Código de idioma desconocido: '%s'. Usa --list-languages para ver "
        "los %d códigos soportados (ej.: es, en, fr).",
        code, len(config.SUPPORTED_LANGUAGES))
    sys.exit(config.EXIT_USAGE)


def _will_shorten(kinds: List[str], shorten: bool, output_format: str) -> bool:
    """True when this run will actually touch .srt files."""
    generates_srt = output_format in ("srt", "all")
    return "srt" in kinds or (shorten and generates_srt)


def validate_dependencies(kinds: List[str], shorten: bool, output_format: str,
                          dry_run: bool, logger: Logger) -> None:
    """Checks external tools required by the requested operations only.

    Real runs exit with EXIT_DEPENDENCY; dry runs downgrade to warnings so
    the execution plan is still shown.
    """
    missing = []
    if any(kind in ("url", "media") for kind in kinds):
        # ffmpeg is required by Whisper itself to decode any input.
        missing += [b for b in ("whisper", "ffmpeg") if shutil.which(b) is None]
    if "url" in kinds and shutil.which("yt-dlp") is None:
        missing.append("yt-dlp")
    if _will_shorten(kinds, shorten, output_format) \
            and importlib.util.find_spec("pysrt") is None:
        missing.append("pysrt")
    if not missing:
        return
    report = logger.warning if dry_run else logger.error
    for name in missing:
        report("Falta la dependencia '%s' (instálala con: %s).",
               name, _INSTALL_HINTS[name])
    if dry_run:
        logger.warning("Simulación: se continúa aunque falten dependencias.")
    else:
        sys.exit(config.EXIT_DEPENDENCY)


def validate_shorten_combination(kinds: List[str], shorten: bool,
                                 output_format: str, logger: Logger) -> None:
    """Warns when --shorten-srt cannot act because no .srt will exist."""
    if shorten and not _will_shorten(kinds, shorten, output_format):
        logger.warning(
            "--shorten-srt no tendrá efecto: con --output-format %s no se "
            "genera ningún .srt.", output_format)


def validate_output_dir(raw: str, dry_run: bool, logger: Logger) -> Path:
    """Ensures the output directory exists (creating it) and is writable."""
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
