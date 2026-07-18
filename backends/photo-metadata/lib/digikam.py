"""Sincroniza la fecha EXIF desde la base de datos de digiKam.

Para fotos escaneadas el usuario corrigió las fechas DENTRO de digiKam, así
que ahí la verdad es `digikam4.db` (ImageInformation.creationDate), no el
nombre del archivo (que suele ser la fecha del escaneo). La base se copia a
un archivo temporal y se abre SOLO en lectura: la original nunca se toca.
"""
from __future__ import annotations

import shutil
import sqlite3
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from config import Settings
from lib import audit
from lib.errors import DependencyError


def _find_database(folder: Path, settings: Settings) -> Path:
    """La BD vive en la raíz de la colección (la carpeta padre del álbum)."""
    for candidate in (folder.parent / settings.digikam_db_name,
                      folder / settings.digikam_db_name):
        if candidate.is_file():
            return candidate
    raise DependencyError(
        f"No se encontró {settings.digikam_db_name} junto a {folder}")


def _parse_db_date(value: str | None) -> datetime | None:
    """Fechas de digiKam: 'AAAA-MM-DDTHH:MM:SS(.mmm)(Z)'; se toman literales."""
    if not value:
        return None
    try:
        return datetime.strptime(value.replace("T", " ")[:19],
                                 "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def read_album_dates(folder: Path, settings: Settings) -> dict[str, datetime]:
    """{nombre: fecha_digikam} del álbum que corresponde a la carpeta."""
    source = _find_database(folder, settings)
    with tempfile.NamedTemporaryFile(suffix=".db") as handle:
        shutil.copyfile(source, handle.name)
        connection = sqlite3.connect(f"file:{handle.name}?mode=ro", uri=True)
        try:
            query = ("SELECT i.name, ii.creationDate "
                     "FROM Images i "
                     "JOIN Albums a ON i.album = a.id "
                     "JOIN ImageInformation ii ON ii.imageid = i.id "
                     "WHERE a.relativePath = ? AND ii.creationDate IS NOT NULL")
            rows = connection.execute(query, (f"/{folder.name}",)).fetchall()
        finally:
            connection.close()
    dates = {}
    for name, value in rows:
        moment = _parse_db_date(value)
        if moment is not None:
            dates[name] = moment
    return dates


def build_sync_plan(folder: Path, settings: Settings
                    ) -> list[tuple[str, datetime | None, datetime]]:
    """(nombre, exif_actual, fecha_digikam) donde difieren más que la tolerancia."""
    db_dates = read_album_dates(folder, settings)
    plan = []
    for meta in audit.read_metadata(folder, settings):
        name = meta.get("FileName", "")
        target = db_dates.get(name)
        if target is None:
            continue
        current = audit.primary_meta_date(meta)
        if current and abs((current - target).total_seconds()) \
                <= settings.audit_tolerance_seconds:
            continue
        plan.append((name, current, target))
    return sorted(plan)


def apply_sync(folder: Path, plan: list, settings: Settings
               ) -> subprocess.CompletedProcess | None:
    """Escribe las fechas de digiKam vía argfile (un solo proceso de exiftool)."""
    if not plan:
        return None
    lines: list[str] = []
    for name, _current, target in plan:
        stamp = target.strftime("%Y:%m:%d %H:%M:%S")
        lines += [f"-AllDates={stamp}"]
        if settings.set_file_modify_date:
            lines.append(f"-FileModifyDate={stamp}")
        lines += [str(folder / name), "-execute"]
    with tempfile.NamedTemporaryFile("w", suffix=".args", delete=False,
                                     encoding="utf-8") as handle:
        handle.write("\n".join(lines))
        argfile = handle.name
    try:
        return subprocess.run(
            [settings.exiftool_binary, "-@", argfile,
             "-common_args", "-overwrite_original"],
            capture_output=True, text=True, check=False)
    finally:
        Path(argfile).unlink(missing_ok=True)
