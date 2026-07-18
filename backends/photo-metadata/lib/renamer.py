"""Renombrado seguro en dos fases, con registro reversible y script de deshacer.

El renombrado en dos fases (origen -> temporal -> destino) permite intercambios
de nombres (A->B mientras B->C) sin sobrescribir ningún archivo intermedio.
"""
from __future__ import annotations

import csv
import os
from pathlib import Path

from config import Settings
from lib.errors import PlanError
from lib.planner import PlanEntry


def _rename_pairs(entries: list[PlanEntry]) -> list[tuple[str, str]]:
    """Extrae los pares (origen, destino) de las filas marcadas RENAME."""
    return [(entry.old, entry.new) for entry in entries if entry.action == "RENAME"]


def _verify_safe(pairs: list[tuple[str, str]], folder: Path) -> None:
    """Comprueba precondiciones que garantizan un renombrado sin pérdidas.

    Raises:
        FileNotFoundError: Si falta algún archivo de origen.
        PlanError: Si hay destinos duplicados o alguno sobrescribiría un archivo
            que no forma parte del renombrado.
    """
    missing = [src for src, _ in pairs if not (folder / src).exists()]
    if missing:
        raise FileNotFoundError(f"Faltan archivos de origen: {missing[:5]}")
    destinations = [dst for _, dst in pairs]
    if len(destinations) != len(set(destinations)):
        raise PlanError("El plan tiene nombres de destino duplicados.")
    sources = {src for src, _ in pairs}
    for _, dst in pairs:
        if (folder / dst).exists() and dst not in sources:
            raise PlanError(f"El destino '{dst}' ya existe y sobrescribiría datos.")


def safe_two_phase(pairs: list[tuple[str, str]], folder: Path,
                   temp_prefix: str) -> None:
    """Renombra en dos fases (origen -> temporal -> destino)."""
    temp_map: dict[Path, Path] = {}
    for index, (src, dst) in enumerate(pairs):
        temp = folder / f"{temp_prefix}{index}{Path(src).suffix}"
        (folder / src).rename(temp)
        temp_map[temp] = folder / dst
    for temp, target in temp_map.items():
        if target.exists():
            raise PlanError(f"Destino inesperado ya existente: '{target.name}'.")
        temp.rename(target)


def _write_log(pairs: list[tuple[str, str]], folder: Path, settings: Settings) -> Path:
    """Guarda el registro reversible 'viejo,nuevo' de los cambios aplicados."""
    log_path = folder / settings.log_csv_name
    with log_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["old", "new"])
        writer.writerows(pairs)
    return log_path


def _write_undo_script(pairs: list[tuple[str, str]], folder: Path,
                       settings: Settings) -> Path:
    """Genera un script bash que revierte el renombrado (también en dos fases)."""
    undo_path = folder / settings.undo_script_name
    lines = ["#!/usr/bin/env bash",
             "# Revierte el ultimo renombrado. Ejecutar dentro de la carpeta.",
             'cd "$(dirname "$0")" || exit 1']
    for index, (src, dst) in enumerate(pairs):
        temp = f".__undo_{index}__{Path(dst).suffix}"
        lines.append(f'mv -n -- "{dst}" "{temp}"')
    for index, (src, dst) in enumerate(pairs):
        temp = f".__undo_{index}__{Path(dst).suffix}"
        lines.append(f'mv -n -- "{temp}" "{src}"')
    undo_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    undo_path.chmod(0o755)
    return undo_path


def apply_plan(entries: list[PlanEntry], folder: Path, settings: Settings,
               execute: bool) -> list[tuple[str, str]]:
    """Aplica el plan. Sin `execute` solo simula (no toca archivos).

    Returns:
        La lista de pares (origen, destino) que se renombran (o renombrarían).
    """
    pairs = _rename_pairs(entries)
    _verify_safe(pairs, folder)
    if not execute:
        return pairs
    safe_two_phase(pairs, folder, settings.temp_prefix)
    _write_log(pairs, folder, settings)
    _write_undo_script(pairs, folder, settings)
    return pairs


def undo_from_log(folder: Path, settings: Settings, execute: bool
                  ) -> list[tuple[str, str]]:
    """Revierte usando el log CSV. Sin `execute` solo simula.

    Raises:
        FileNotFoundError: Si no existe el log de un renombrado previo.
    """
    log_path = folder / settings.log_csv_name
    if not log_path.exists():
        raise FileNotFoundError(f"No hay registro para deshacer: '{log_path}'.")
    with log_path.open(newline="", encoding="utf-8") as handle:
        reverse = [(row["new"], row["old"]) for row in csv.DictReader(handle)]
    _verify_safe(reverse, folder)
    if execute:
        safe_two_phase(reverse, folder, settings.temp_prefix)
        os.remove(log_path)
    return reverse
