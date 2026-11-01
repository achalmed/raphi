"""SRT line-length reformatting for whisper-transcriber.

The original notebook did `sub.text = sub.text[:37]`, silently DELETING
everything past the first 37 characters of each subtitle. Here the full
text is preserved and re-wrapped at word boundaries into lines of at
most N characters (37 by default — the BBC subtitling guideline the
notebook cited). The result is written next to the source with a suffix;
the source .srt is never modified.
"""
from __future__ import annotations

import textwrap
from logging import Logger
from pathlib import Path
from typing import Optional

import config


def wrap_subtitle_text(text: str, max_line_length: int) -> str:
    """Re-wraps subtitle text at word boundaries, preserving every word.

    Existing line breaks are treated as spaces before re-wrapping. Words
    longer than the limit are kept whole: an occasional long line reads
    better than a mid-word cut.
    """
    normalized = " ".join(text.split())
    if not normalized:
        return ""
    lines = textwrap.wrap(normalized, width=max_line_length,
                          break_long_words=False, break_on_hyphens=False)
    return "\n".join(lines)


def shortened_target(srt_path: Path) -> Path:
    """entrada.srt -> entrada_acortado.srt (same directory)."""
    return srt_path.with_name(
        f"{srt_path.stem}{config.SHORTENED_SUFFIX}{srt_path.suffix}")


def shorten_srt_file(srt_path: Path, max_line_length: int, logger: Logger,
                     dry_run: bool = False) -> Optional[Path]:
    """Rewraps every subtitle of an .srt file into a new *_acortado.srt.

    Returns:
        Path of the shortened file, or None on failure/dry-run.
    """
    target = shortened_target(srt_path)
    if dry_run:
        logger.info("[SIMULACIÓN] Acortaría '%s' a líneas de <=%d "
                    "caracteres -> '%s'.", srt_path, max_line_length, target)
        return None
    # Lazy import: pysrt is only needed for this optional feature
    # (lib/validator.py already verified it when the run requires it).
    import pysrt
    try:
        subtitles = pysrt.open(str(srt_path))
    except (OSError, UnicodeDecodeError) as error:
        logger.error("No se pudo leer el subtítulo '%s': %s", srt_path, error)
        return None
    changed = 0
    for subtitle in subtitles:
        wrapped = wrap_subtitle_text(subtitle.text, max_line_length)
        if wrapped != subtitle.text:
            subtitle.text = wrapped
            changed += 1
    subtitles.save(str(target), encoding="utf-8")
    logger.info("Subtítulo acortado (%d de %d bloques reformateados): %s",
                changed, len(subtitles), target)
    return target
