"""Construcción del plan de renombrado a partir de los resultados de OCR.

Cada archivo con sello se mapea a 'AAAAMMDD_HHMMSS.ext'. Cuando dos o más
fotos comparten el mismo sello y extensión (ráfagas/duplicados) se añade un
sufijo '_2', '_3'... para que ningún nombre se pierda.
"""
from __future__ import annotations

import csv
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from lib.ocr import OcrResult

_BASE_STEM = re.compile(r"\d{8}_\d{6}$")  # AAAAMMDD_HHMMSS sin sufijo de colisión


@dataclass
class PlanEntry:
    """Una fila del plan: qué archivo pasa a qué nombre y por qué."""

    old: str
    new: str
    stamp: str
    status: str
    action: str  # RENAME | KEEP | SKIP


def _assign_targets(resolved: dict[str, OcrResult]) -> dict[str, str]:
    """Asigna un nombre destino único por archivo, resolviendo colisiones."""
    groups: dict[tuple, list[str]] = defaultdict(list)
    for path, result in resolved.items():
        groups[(result.stamp, Path(path).suffix)].append(path)
    targets: dict[str, str] = {}
    for (stamp, extension), files in groups.items():
        for index, path in enumerate(sorted(files)):
            stem = stamp if index == 0 else f"{stamp}_{index + 1}"
            targets[path] = stem + extension
    return targets


def _make_entry(result: OcrResult, target_name: str) -> PlanEntry:
    """Crea una fila marcando KEEP si el nombre ya es el correcto."""
    current_name = Path(result.file).name
    action = "KEEP" if target_name == current_name else "RENAME"
    return PlanEntry(current_name, target_name, result.stamp, result.status, action)


def build_plan(results: list[OcrResult]) -> list[PlanEntry]:
    """Convierte los resultados de OCR en un plan ordenado y sin colisiones.

    Los archivos sin sello legible se incluyen como SKIP (no se tocan).
    """
    resolved = {r.file: r for r in results if r.stamp}
    targets = _assign_targets(resolved)
    entries = [_make_entry(result, targets[path])
               for path, result in resolved.items()]
    entries += [PlanEntry(Path(r.file).name, Path(r.file).name, "", r.status, "SKIP")
                for r in results if not r.stamp]
    entries.sort(key=lambda entry: entry.old)
    return entries


def write_plan_csv(entries: list[PlanEntry], csv_path: Path) -> None:
    """Escribe el plan a CSV (editable a mano antes de aplicar)."""
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["old", "new", "stamp", "status", "action"])
        for entry in entries:
            writer.writerow([entry.old, entry.new, entry.stamp,
                             entry.status, entry.action])


def read_plan_csv(csv_path: Path) -> list[PlanEntry]:
    """Lee un plan (posiblemente editado por el usuario) desde CSV."""
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [PlanEntry(row["old"], row["new"], row.get("stamp", ""),
                      row.get("status", ""),
                      "KEEP" if row["new"] == row["old"] else row.get("action", "RENAME"))
            for row in rows]


def summarize(entries: list[PlanEntry]) -> dict[str, int]:
    """Devuelve conteos por acción y colisiones para el resumen final."""
    renames = [e for e in entries if e.action == "RENAME"]
    collisions = sum(1 for e in renames if not _BASE_STEM.fullmatch(Path(e.new).stem))
    return {
        "total": len(entries),
        "rename": len(renames),
        "keep": sum(1 for e in entries if e.action == "KEEP"),
        "skip": sum(1 for e in entries if e.action == "SKIP"),
        "collision_suffixed": collisions,
    }
