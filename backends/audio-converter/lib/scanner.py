"""Audio discovery and conversion planning for audio-converter.

Turns the CLI inputs (files and/or directories) into a deduplicated
(source, target) work plan. Directories are filtered by the WhatsApp-
oriented extension list in config.py; explicitly named files are taken
as-is because the user knows better than the filter.
"""
from __future__ import annotations

from logging import Logger
from pathlib import Path
from typing import List, Optional, Tuple

import config


def _scan_directory(directory: Path, recursive: bool,
                    logger: Logger) -> List[Path]:
    """Collects convertible audio files inside a directory."""
    pattern = "**/*" if recursive else "*"
    found = [path for path in sorted(directory.glob(pattern))
             if path.is_file()
             and path.suffix.lower() in config.AUDIO_EXTENSIONS]
    if found:
        logger.info("Encontrados %d audio(s) en '%s'.", len(found), directory)
    else:
        hint = "" if recursive else " (prueba -r para incluir subcarpetas)"
        logger.warning("Sin audios convertibles en '%s'%s.", directory, hint)
    return found


def discover_audio_files(inputs: List[Path], recursive: bool,
                         logger: Logger) -> List[Path]:
    """Expands files/directories into a deduplicated list of sources."""
    sources: List[Path] = []
    for path in inputs:
        if path.is_dir():
            sources.extend(_scan_directory(path, recursive, logger))
        elif path.suffix.lower() == config.TARGET_EXTENSION:
            logger.warning("'%s' ya es %s; se omite.",
                           path.name, config.TARGET_EXTENSION)
        else:
            if path.suffix.lower() not in config.AUDIO_EXTENSIONS:
                logger.debug("Extensión '%s' fuera de la lista típica; "
                             "ffmpeg decidirá si puede decodificar '%s'.",
                             path.suffix, path.name)
            sources.append(path)
    unique, seen = [], set()
    for path in sources:
        key = path.resolve()
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def plan_conversions(sources: List[Path], output_dir: Optional[Path],
                     logger: Logger) -> List[Tuple[Path, Path]]:
    """Maps each source to its .mp3 target, refusing duplicate targets.

    Two different sources can collapse into the same target when a shared
    --output-dir flattens directories (a.opus and a.ogg -> a.mp3); the
    first one wins and the rest are skipped loudly.
    """
    plan, taken = [], set()
    for source in sources:
        target_dir = output_dir if output_dir is not None else source.parent
        target = target_dir / (source.stem + config.TARGET_EXTENSION)
        key = str(target.resolve())
        if key in taken:
            logger.warning("Destino duplicado '%s'; se omite '%s'.",
                           target.name, source)
            continue
        taken.add(key)
        plan.append((source, target))
    return plan
