#!/usr/bin/env python3
"""whisper-transcriber — transcripción y traducción de audio/video con Whisper.

Modular CLI rebuild of the Colab notebook "Transcribir y Traducir OpenAI
Whisper" (Jason Boog; mods. Álex Goia; MIT). Orchestration only — the
logic lives in lib/:

  1. Parse arguments          (lib/cli.py)
  2. Init logging             (lib/logger.py)
  3. Validate everything      (lib/validator.py)
  4. Process each input:
       URL   -> download audio  (lib/downloader.py)  -> Whisper
       media -> transcribe/translate                 (lib/transcriber.py)
       .srt  -> shorten lines                        (lib/subtitle_shortener.py)
  5. Summary and temporary-file cleanup.

Version: 1.0.0
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # run from any CWD

import config
from lib import validator
from lib.cli import build_argument_parser
from lib.downloader import download_audio
from lib.logger import setup_logger
from lib.subtitle_shortener import shorten_srt_file
from lib.transcriber import transcribe_file


def print_language_catalog() -> None:
    """Prints the language table to stdout (data output, not logging)."""
    print(f"Idiomas soportados por --language "
          f"({len(config.SUPPORTED_LANGUAGES)} códigos):")
    def alphabetical(pair):
        # Codepoint sort sends 'Árabe' past 'Zulú'. NFKD splits Á into
        # A + combining accent; dropping the accents makes the sort Spanish-
        # alphabetical without depending on the system locale.
        decomposed = unicodedata.normalize("NFKD", pair[1])
        return "".join(char for char in decomposed
                       if not unicodedata.combining(char)).casefold()

    for code, name in sorted(config.SUPPORTED_LANGUAGES.items(),
                             key=alphabetical):
        print(f"  {code:<4} {name}")


def shorten_generated_srt(produced, args, logger):
    """Applies --shorten-srt to the .srt files produced in this run."""
    if args.dry_run:
        if args.output_format in ("srt", "all"):
            logger.info("[SIMULACIÓN] Acortaría el .srt generado a líneas "
                        "de <=%d caracteres.", args.max_line_length)
        return []
    shortened = []
    for srt_path in [p for p in produced if p.suffix == ".srt"]:
        target = shorten_srt_file(srt_path, args.max_line_length, logger)
        if target is not None:
            shortened.append(target)
    return shortened


def process_input(kind, item, args, output_dir, download_dir, logger):
    """Runs the pipeline for one input. Returns produced paths or None."""
    if kind == "srt":
        target = shorten_srt_file(item, args.max_line_length, logger,
                                  args.dry_run)
        return [] if args.dry_run else ([target] if target else None)
    media_path = item
    if kind == "url":
        keep_dir = output_dir if args.keep_audio else None
        media_path = download_audio(item, download_dir, logger,
                                    args.dry_run, keep_dir)
        if media_path is None:
            if not args.dry_run:
                return None
            media_path = Path("AUDIO_DESCARGADO.mp3")  # placeholder del plan
    produced = transcribe_file(media_path, args.task, args.model,
                               args.language, output_dir,
                               args.output_format, logger, args.dry_run)
    if produced is None:
        return None
    if args.shorten_srt:
        produced = produced + shorten_generated_srt(produced, args, logger)
    return produced


def print_summary(logger, total, failures, generated, dry_run) -> None:
    """Final report: processed counts and files written."""
    if dry_run:
        logger.info("Simulación terminada: %d entrada(s) analizada(s); "
                    "no se ejecutó nada.", total)
        return
    logger.info("Resumen: %d/%d entrada(s) procesada(s) correctamente; "
                "%d archivo(s) generado(s).",
                total - failures, total, len(generated))
    if failures:
        logger.error("%d entrada(s) fallaron; revisa los mensajes anteriores.",
                     failures)


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()
    if args.list_languages:
        print_language_catalog()
        return config.EXIT_OK
    if not args.inputs:
        parser.error("se requiere al menos una ENTRADA "
                     "(o usa --list-languages)")
    logger = setup_logger(config.APP_NAME, args.verbose, config.LOG_FILE)
    if args.dry_run:
        logger.info("Modo simulación: no se descargará, transcribirá "
                    "ni escribirá nada.")
    validator.validate_language(args.language, logger)
    inputs = validator.validate_inputs(args.inputs, logger)
    kinds = [kind for kind, _ in inputs]
    validator.validate_dependencies(kinds, args.shorten_srt,
                                    args.output_format, args.dry_run, logger)
    validator.validate_shorten_combination(kinds, args.shorten_srt,
                                           args.output_format, logger)
    output_dir = validator.validate_output_dir(args.output_dir,
                                               args.dry_run, logger)
    needs_temp = "url" in kinds and not args.dry_run
    temp_root = (Path(tempfile.mkdtemp(prefix="whisper-transcriber-"))
                 if needs_temp else None)
    failures = 0
    generated = []
    try:
        for index, (kind, item) in enumerate(inputs, start=1):
            download_dir = ((temp_root or Path("(directorio-temporal)"))
                            / f"descarga_{index}")
            result = process_input(kind, item, args, output_dir,
                                   download_dir, logger)
            if result is None:
                failures += 1
            else:
                generated.extend(result)
    finally:
        if temp_root is not None:
            # Downloaded audio is temporary unless --keep-audio moved it out.
            shutil.rmtree(temp_root, ignore_errors=True)
    print_summary(logger, len(inputs), failures, generated, args.dry_run)
    return config.EXIT_OK if failures == 0 else config.EXIT_GENERAL


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario.", file=sys.stderr)
        sys.exit(130)  # convención del shell para SIGINT
