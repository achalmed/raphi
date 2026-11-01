"""Escribe la fecha de captura en los metadatos, derivada del nombre del archivo.

Usa exiftool. En fotos escribe las fechas EXIF (DateTimeOriginal, CreateDate,
ModifyDate); en videos, las fechas QuickTime. Así apps como digiKam agrupan por
la fecha real de captura en vez de por una fecha del sistema de archivos.

Hay dos pases: el estándar (nombres AAAAMMDD_HHMMSS, vía expresión de
exiftool) y el especial (WhatsApp, fb_<epoch>, fecha parcial), donde la fecha
se calcula en Python porque el nombre no trae hora o usa otro formato. La
fecha SIEMPRE sale del nombre del archivo, nunca del sistema de archivos:
las fechas de modificación cambian con cada copia y no son confiables.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from config import Settings
from lib import audit

# Solo se tocan archivos cuyo nombre empieza por AAAAMMDD_HHMMSS.
_NAME_CONDITION = r"$filename =~ /^\d{8}_\d{6}/"
# Fecha principal existente según exiftool ('0000...' cuenta como ausente).
_PRIMARY = "($DateTimeOriginal || $CreateDate)"
_PRIMARY_MISSING = f'({_PRIMARY} || "0000") =~ /^0000/'
# Día de la fecha principal como dígitos 'AAAAMMDD' (evita usar $1/$2: exiftool
# interpola los $n de -if como etiquetas y rompe la expresión).
_PRIMARY_DAY = (f"substr({_PRIMARY},0,4) . substr({_PRIMARY},5,2)"
                f" . substr({_PRIMARY},8,2)")
_SUMMARY = re.compile(r"\d+ (?:image|video)? ?files? (?:updated|unchanged)")

# Patrones de nombre (ver lib/audit.py) que atiende el pase especial.
_SPECIAL_PATTERNS = {"whatsapp", "whatsapp-original", "facebook-epoch",
                     "fecha-parcial"}


def _tag_assignments(tags: tuple, expr: str) -> list[str]:
    """Construye los argumentos '-Tag<EXPRESIÓN' para cada etiqueta de fecha."""
    return [f"-{tag}<{expr}" for tag in tags]


def _ext_flags(extensions: tuple) -> list[str]:
    """Traduce las extensiones a flags '-ext EXT' de exiftool."""
    flags: list[str] = []
    for extension in extensions:
        flags += ["-ext", extension.lstrip(".")]
    return flags


def _run(folder: Path, tags: tuple, extensions: tuple, settings: Settings,
         extra: list[str] | None = None) -> subprocess.CompletedProcess:
    """Ejecuta exiftool sobre la carpeta (no recursivo) con las etiquetas dadas."""
    command = [settings.exiftool_binary, "-overwrite_original",
               "-if", _NAME_CONDITION]
    command += extra or []
    command += _ext_flags(extensions)
    command += _tag_assignments(tags, settings.filename_date_expr)
    command.append(str(folder))
    return subprocess.run(command, capture_output=True, text=True, check=False)


def _write_condition(settings: Settings, day: str | None = None) -> str:
    """Condición perl de escritura: ¿cuándo manda la fecha del nombre?

    Se escribe si no hay fecha EXIF, o si la existente es POSTERIOR al día
    del nombre Y no trae cámara (Make/Model): sin cámara es un artefacto de
    copia. Con Make/Model podría ser la captura real aunque sea posterior —
    los nombres puestos a mano "a ojo" no son confiables como cota — así que
    se respeta y la auditoría lo deja para revisión. Un EXIF anterior se
    respeta siempre. `day` son dígitos 'AAAAMMDD' cuando ya se conoce (pase
    especial); si es None se extrae del propio nombre.
    """
    if settings.trust_name:
        return "1"  # modo escaneadas: el nombre manda sobre cualquier EXIF
    name_day = f'"{day}"' if day else "substr($filename,0,8)"
    later = (f"({_PRIMARY_DAY} gt {name_day}"
             f" and not $Make and not $Model)")
    if not settings.overwrite_later_exif:
        later = "0"
    conditions = [_PRIMARY_MISSING, later]
    if day is None:
        # Medianoche exacta = placeholder embebido cuando el nombre solo traía
        # el día; si el nombre ahora tiene hora real (p.ej. tras convertir un
        # nombre 12h con fix-names), la hora del nombre manda.
        conditions.append(f'(substr({_PRIMARY},11,8) eq "00:00:00"'
                          f' and substr($filename,9,6) ne "000000")')
    return f"({' or '.join(conditions)})"


def _missing_only(settings: Settings) -> list[str]:
    """Flags '-if' extra si solo debe escribirse donde falte la fecha."""
    if settings.embed_only_missing:
        return ["-if", _write_condition(settings)]
    return []


def embed_image_dates(folder: Path, settings: Settings
                      ) -> subprocess.CompletedProcess:
    """Escribe las fechas EXIF de las fotos desde su nombre."""
    extensions = settings.image_extensions + settings.extra_audit_extensions
    return _run(folder, settings.image_date_tags, extensions, settings,
                extra=_missing_only(settings))


def embed_video_dates(folder: Path, settings: Settings
                      ) -> subprocess.CompletedProcess:
    """Escribe las fechas QuickTime de los videos desde su nombre.

    QuickTimeUTC=0 guarda la hora local tal cual (sin conversión a UTC).
    """
    return _run(folder, settings.video_date_tags, settings.video_extensions,
                settings,
                extra=["-api", "QuickTimeUTC=0"] + _missing_only(settings))


def special_targets(folder: Path, settings: Settings
                    ) -> list[tuple[Path, str]]:
    """Pares (archivo, 'AAAA:MM:DD HH:MM:SS') del pase especial.

    Cubre nombres que el pase estándar no entiende: WhatsApp (solo día, la
    hora queda en 00:00:00 porque el nombre no la trae), fb_<epoch-ms> y
    fechas parciales. La fecha sale exclusivamente del nombre.
    """
    extensions = (set(settings.image_extensions) | set(settings.video_extensions)
                  | set(settings.extra_audit_extensions))
    targets = []
    for entry in sorted(folder.iterdir()):
        if not entry.is_file() or entry.suffix.lower() not in extensions:
            continue
        pattern, stamp, _precision = audit.parse_name_date(entry.name)
        if pattern in _SPECIAL_PATTERNS and stamp is not None:
            targets.append((entry, stamp.strftime("%Y:%m:%d %H:%M:%S")))
    return targets


def embed_special_dates(folder: Path, settings: Settings
                        ) -> subprocess.CompletedProcess | None:
    """Escribe la fecha del nombre en los archivos del pase especial.

    Un solo proceso de exiftool vía argfile (-@), un comando por archivo.
    Solo escribe donde no hay DateTimeOriginal ni CreateDate.
    """
    targets = special_targets(folder, settings)
    if not targets:
        return None
    lines: list[str] = []
    for path, stamp in targets:
        tags = (settings.video_date_tags
                if path.suffix.lower() in settings.video_extensions
                else settings.image_date_tags)
        lines += ["-if", _write_condition(settings,
                                          day=stamp[:10].replace(":", ""))]
        lines += [f"-{tag}={stamp}" for tag in tags]
        if settings.set_file_modify_date:
            lines.append(f"-FileModifyDate={stamp}")
        lines += [str(path), "-execute"]
    with tempfile.NamedTemporaryFile("w", suffix=".args", delete=False,
                                     encoding="utf-8") as handle:
        handle.write("\n".join(lines))
        argfile = handle.name
    try:
        # OJO: -common_args NO funciona dentro de un argfile (exiftool lo
        # ignora y crearía respaldos *_original); debe ir en la línea de
        # comandos, después de -@.
        command = [settings.exiftool_binary, "-@", argfile,
                   "-common_args", "-overwrite_original",
                   "-api", "QuickTimeUTC=0"]
        return subprocess.run(command, capture_output=True, text=True, check=False)
    finally:
        Path(argfile).unlink(missing_ok=True)


def embed_file_modify_date(folder: Path, settings: Settings, extensions: tuple
                           ) -> subprocess.CompletedProcess:
    """Fija FileModifyDate (fecha del sistema) desde el nombre.

    Es una operación de sistema de archivos: funciona en cualquier formato,
    incluso los que no admiten metadatos embebidos (p.ej. M2TS).
    """
    return _run(folder, ("FileModifyDate",), extensions, settings)


def summarize(result: subprocess.CompletedProcess) -> str:
    """Extrae la línea de resumen de exiftool ('N files updated')."""
    text = f"{result.stdout}\n{result.stderr}"
    matches = _SUMMARY.findall(text)
    if matches:
        return "; ".join(matches)
    return "sin cambios"


def summarize_special(result: subprocess.CompletedProcess | None) -> str:
    """Resume los lotes del argfile: actualizados vs saltados (ya tenían fecha)."""
    if result is None:
        return "sin archivos que atender"
    text = f"{result.stdout}\n{result.stderr}"
    updated = sum(int(n) for n in re.findall(r"(\d+) (?:image|video)? ?files? updated",
                                             text))
    skipped = sum(int(n) for n in re.findall(r"(\d+) files failed condition", text))
    return (f"{updated} actualizados; {skipped} saltados "
            f"(fecha existente correcta o anterior al nombre)")
