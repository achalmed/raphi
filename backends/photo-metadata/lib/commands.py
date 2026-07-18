"""Implementación de cada subcomando. `main.py` solo orquesta estas funciones."""
from __future__ import annotations

import dataclasses
import json
import logging
import re
from pathlib import Path

from config import Settings
from lib import (audit, digikam, fixer, metadata, montage, planner, renamer,
                 scanner, validator)
from lib.planner import PlanEntry

_REVIEW_STATUSES = {"weak", "dark", "fail", "error"}
_NAME_PATTERN = re.compile(r"^\d{8}_\d{6}")


def _prepare(folder_arg: str, settings: Settings) -> Path:
    """Valida dependencias, carpeta y parámetros antes de cualquier lógica."""
    validator.require_tesseract()
    validator.validate_crop(settings)
    folder = validator.validate_folder(folder_arg)
    if scanner.has_videos(folder, settings):
        # ffmpeg solo es imprescindible cuando hay videos que procesar.
        validator.require_ffmpeg(settings.ffmpeg_binary)
    return folder


def _progress(logger: logging.Logger):
    """Crea un callback de progreso que reporta avance y velocidad."""
    def report(done: int, total: int) -> None:
        logger.info("Procesadas %d/%d imágenes (%.0f%%)",
                    done, total, 100 * done / total)
    return report


def _write_analysis(results, folder: Path, settings: Settings) -> None:
    """Vuelca el resultado crudo del OCR a JSON para inspección/depuración."""
    payload = [dataclasses.asdict(result) for result in results]
    (folder / settings.analysis_json_name).write_text(
        json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")


def _log_summary(logger: logging.Logger, entries: list[PlanEntry]) -> None:
    """Imprime el bloque de resumen del plan."""
    stats = planner.summarize(entries)
    logger.info("── Resumen ─────────────────────────────")
    logger.info("Total analizadas : %d", stats["total"])
    logger.info("A renombrar      : %d", stats["rename"])
    logger.info("Ya correctas     : %d", stats["keep"])
    logger.info("Sin marca (SKIP) : %d", stats["skip"])
    logger.info("Con sufijo _N    : %d", stats["collision_suffixed"])
    logger.info("────────────────────────────────────────")


def _scan_and_plan(folder: Path, settings: Settings,
                   logger: logging.Logger) -> list[PlanEntry]:
    """Escanea la carpeta y construye el plan, escribiendo también el JSON."""
    results = scanner.scan_folder(folder, settings, _progress(logger))
    _write_analysis(results, folder, settings)
    return planner.build_plan(results)


def cmd_analyze(folder_arg: str, settings: Settings, logger: logging.Logger) -> int:
    """Analiza la carpeta y escribe el plan y el JSON. No cambia nada."""
    folder = _prepare(folder_arg, settings)
    entries = _scan_and_plan(folder, settings, logger)
    planner.write_plan_csv(entries, folder / settings.plan_csv_name)
    _log_summary(logger, entries)
    logger.info("Plan escrito en: %s", folder / settings.plan_csv_name)
    return 0


def cmd_apply(folder_arg: str, settings: Settings, logger: logging.Logger,
              execute: bool, from_plan: str | None) -> int:
    """Renombra según el plan. Sin `execute` solo simula."""
    folder = _prepare(folder_arg, settings)
    if from_plan:
        entries = planner.read_plan_csv(Path(from_plan))
    else:
        entries = _scan_and_plan(folder, settings, logger)
        planner.write_plan_csv(entries, folder / settings.plan_csv_name)
    _log_summary(logger, entries)
    pairs = renamer.apply_plan(entries, folder, settings, execute)
    if execute:
        logger.info("Renombrado aplicado: %d archivos. Log y undo creados.", len(pairs))
    else:
        logger.warning("[SIMULACIÓN] %d se renombrarían. Añade --execute para aplicar.",
                       len(pairs))
    return 0


def _review_items(entries: list[PlanEntry], folder: Path
                  ) -> list[tuple[str, Path]]:
    """Selecciona filas dudosas o con colisión y arma las etiquetas del montaje."""
    stamps = [entry.stamp for entry in entries]
    chosen = [entry for entry in entries
              if entry.status in _REVIEW_STATUSES
              or (entry.stamp and stamps.count(entry.stamp) > 1)]
    return [(f"{entry.old}\n-> {entry.new}\n[{entry.status}]", folder / entry.old)
            for entry in chosen]


def cmd_verify(folder_arg: str, settings: Settings, logger: logging.Logger,
               from_plan: str | None) -> int:
    """Genera montajes PNG de las lecturas dudosas y las colisiones."""
    folder = _prepare(folder_arg, settings)
    entries = (planner.read_plan_csv(Path(from_plan)) if from_plan
               else _scan_and_plan(folder, settings, logger))
    items = _review_items(entries, folder)
    if not items:
        logger.info("No hay lecturas dudosas ni colisiones que revisar.")
        return 0
    outputs = montage.build_montages_chunked(items, folder, "verify_review", settings)
    logger.info("Montajes de revisión: %s", ", ".join(str(path) for path in outputs))
    return 0


def cmd_undo(folder_arg: str, settings: Settings, logger: logging.Logger,
             execute: bool) -> int:
    """Revierte el último renombrado usando el registro guardado."""
    folder = validator.validate_folder(folder_arg)
    pairs = renamer.undo_from_log(folder, settings, execute)
    if execute:
        logger.info("Renombrado revertido: %d archivos.", len(pairs))
    else:
        logger.warning("[SIMULACIÓN] %d se revertirían. Añade --execute.", len(pairs))
    return 0


def _count_scope(folder: Path, settings: Settings) -> dict[str, int]:
    """Cuenta fotos y videos con nombre AAAAMMDD_HHMMSS a los que se escribiría."""
    images = set(settings.image_extensions)
    videos = set(settings.video_extensions)
    counts = {"images": 0, "videos": 0}
    for entry in folder.iterdir():
        if not (entry.is_file() and _NAME_PATTERN.match(entry.name)):
            continue
        suffix = entry.suffix.lower()
        if suffix in images:
            counts["images"] += 1
        elif suffix in videos:
            counts["videos"] += 1
    return counts


def cmd_embed_date(folder_arg: str, settings: Settings, logger: logging.Logger,
                   execute: bool) -> int:
    """Escribe en los metadatos la fecha de captura tomada del nombre del archivo."""
    validator.require_exiftool(settings.exiftool_binary)
    folder = validator.validate_folder(folder_arg)
    scope = _count_scope(folder, settings)
    special = metadata.special_targets(folder, settings)
    do_images = settings.media_filter in ("all", "images") and scope["images"]
    do_videos = settings.media_filter in ("all", "videos") and scope["videos"]
    if not execute:
        logger.warning("[SIMULACIÓN] recibirían la fecha del nombre: %d fotos, %d "
                       "videos y %d especiales (WhatsApp/fb/parcial); solo se "
                       "escribe donde falte EXIF. Añade --execute.",
                       scope["images"], scope["videos"], len(special))
        for path, stamp in special[:15]:
            logger.info("  especial: %s -> %s", path.name, stamp)
        if len(special) > 15:
            logger.info("  ... y %d especiales más", len(special) - 15)
        return 0
    if do_images:
        logger.info("Fotos: %s", metadata.summarize(
            metadata.embed_image_dates(folder, settings)))
    if do_videos:
        logger.info("Videos: %s", metadata.summarize(
            metadata.embed_video_dates(folder, settings)))
    if special:
        logger.info("Especiales (WhatsApp/fb/parcial): %s",
                    metadata.summarize_special(
                        metadata.embed_special_dates(folder, settings)))
    if settings.set_file_modify_date:
        # Respaldo para formatos sin metadatos (M2TS) y mtime coherente.
        extensions = tuple(scanner.selected_extensions(settings))
        logger.info("Fecha de archivo: %s", metadata.summarize(
            metadata.embed_file_modify_date(folder, settings, extensions)))
    logger.info("Fecha embebida. En digiKam: 'Volver a leer metadatos'.")
    return 0


def cmd_audit_dates(folder_arg: str, settings: Settings, logger: logging.Logger,
                    year: int | None) -> int:
    """Compara la fecha del nombre con los metadatos. No modifica nada."""
    validator.require_exiftool(settings.exiftool_binary)
    folder = validator.validate_folder(folder_arg)
    if year is None and folder.name.isdigit() and len(folder.name) == 4:
        year = int(folder.name)  # carpetas tipo ~/Pictures/2026
    rows = audit.audit_folder(folder, settings, year)
    counts = audit.summarize(rows)
    logger.info("── Auditoría de fechas (%s, año esperado: %s) ──",
                folder.name, year or "sin definir")
    for status, total in counts.most_common():
        logger.info("%-18s: %d", status, total)
    logger.info("Total auditados   : %d", len(rows))
    destination = folder / settings.audit_csv_name
    audit.write_audit_csv(rows, destination)
    logger.info("Detalle por archivo en: %s", destination)
    return 0


def cmd_fix_names(folder_arg: str, settings: Settings, logger: logging.Logger,
                  execute: bool) -> int:
    """Corrige extensiones y normaliza nombres decodificables. Simula por defecto."""
    validator.require_exiftool(settings.exiftool_binary)
    folder = validator.validate_folder(folder_arg)
    fixes = fixer.build_fixes(folder, settings)
    if not fixes:
        logger.info("Nada que corregir: extensiones y nombres ya están bien.")
        return 0
    done = fixer.apply_fixes(folder, fixes, settings, execute)
    for old, new in done:
        logger.info("  %s -> %s", old, new)
    if execute:
        logger.info("Renombrados %d archivos (registro en %s). Considera correr "
                    "embed-date después.", len(done), folder / settings.fix_log_name)
    else:
        logger.warning("[SIMULACIÓN] %d se renombrarían. Añade --execute.", len(done))
    return 0


def cmd_sync_digikam(folder_arg: str, settings: Settings, logger: logging.Logger,
                     execute: bool) -> int:
    """Escribe en el EXIF las fechas corregidas en digiKam. Simula por defecto."""
    validator.require_exiftool(settings.exiftool_binary)
    folder = validator.validate_folder(folder_arg)
    plan = digikam.build_sync_plan(folder, settings)
    if not plan:
        logger.info("EXIF ya coincide con digiKam: nada que sincronizar.")
        return 0
    for name, current, target in plan:
        logger.info("  %s: %s -> %s", name, current or "(sin EXIF)", target)
    if execute:
        digikam.apply_sync(folder, plan, settings)
        logger.info("Sincronizados %d archivos desde digiKam.", len(plan))
    else:
        logger.warning("[SIMULACIÓN] %d se sincronizarían. Añade --execute.",
                       len(plan))
    return 0
