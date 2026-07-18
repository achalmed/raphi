"""Auditoría de fechas: compara el nombre de cada archivo con sus metadatos.

Solo lectura: no modifica ninguna imagen ni los archivos de digiKam. Para cada
archivo se extrae la fecha codificada en el nombre (patrones conocidos: cámara,
WhatsApp, IMG_, capturas, Facebook) y se contrasta con DateTimeOriginal /
CreateDate leídos en un solo pase de exiftool. El resultado es un CSV por
archivo y un resumen por estado.
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from config import Settings
from lib.errors import DependencyError

# Patrones de nombre conocidos, en orden de prioridad. Cada entrada define la
# etiqueta del patrón, la regex que captura la fecha y la precisión con la que
# tiene sentido comparar (WhatsApp solo codifica el día, no la hora).
_PATTERNS: tuple = (
    # 12h ANTES que estándar: '20231204_105920pm' no debe leerse como 10:59.
    ("12h", re.compile(r"^(\d{8})_(\d{1,2})(\d{2})(\d{2})([ap]m)(?:\D|$)", re.I),
     "segundos"),
    ("estándar", re.compile(r"^(\d{8})_(\d{6})"), "segundos"),
    ("whatsapp", re.compile(r"^(\d{8})_wa\d+", re.I), "día"),
    ("IMG_", re.compile(r"^IMG_(\d{8})_(\d{6})", re.I), "segundos"),
    ("whatsapp-original", re.compile(r"^(?:IMG|VID)-(\d{8})-WA\d+", re.I), "día"),
    ("captura", re.compile(r"^Screenshot_(\d{8})-(\d{6})", re.I), "segundos"),
    # fb<epoch> (con o sin '_'): 13 dígitos = milisegundos; 12 = centisegundos.
    ("facebook-epoch", re.compile(r"^fb_?(\d{12,13})(?:\D|$)"), "segundos"),
    ("pixiz", re.compile(  # pixiz-DD-MM-AAAA-HH-MM-SS (montajes de pixiz.com)
        r"^pixiz-(\d{2})-(\d{2})-(\d{4})-(\d{2})-(\d{2})-(\d{2})"), "segundos"),
    ("chatgpt", re.compile(  # chatgpt_image_mes_D_AAAA_HH_MM_SS_am/pm
        r"^chatgpt_image_([a-z]{3})_(\d{1,2})_(\d{4})_(\d{1,2})_(\d{2})_(\d{2})_([ap]m)",
        re.I), "segundos"),
    # 'c360<AAAAMMDD><HHMMSS><ms>': fotos de la app Camera360.
    ("camera360", re.compile(r"^c360(\d{8})(\d{6})\d*\.[^.]+$", re.I),
     "segundos"),
    # '<epoch-ms>.jpg' pelado (13 dígitos, sin prefijo): nombres de Android.
    # El rango se valida al decodificar (2002-2035).
    ("epoch", re.compile(r"^(\d{13})\.[^.]+$"), "segundos"),
    # 'photostudio<epoch-ms>': exportes de la app PhotoStudio.
    ("photostudio", re.compile(r"^photostudio(\d{13})(?:\D|$)", re.I),
     "segundos"),
    # '<snowflake>dmdmhlq...': imagen de Twitter/X = ID del tweet (codifica
    # la fecha de publicación) + nombre del archivo de imagen. La letra tras
    # el ID lo distingue de los concatenados de Facebook (ahí siguen dígitos).
    ("twitter", re.compile(r"^(\d{18,19})(?=[a-z])[a-z0-9_-]+\.[^.]+$", re.I),
     "segundos"),
    # '+<teléfono><AAAAMMDDHHMMSS>': contactos de WhatsApp; los últimos 14
    # dígitos son la fecha (el $ obliga a tomar los del final).
    ("telefono-fecha", re.compile(r"^\+\d*?((?:19|20)\d{6})(\d{6})\.[^.]+$"),
     "segundos"),
    ("fecha-parcial", re.compile(r"^(\d{8})[_\-.]"), "día"),
)
# Descargas de Facebook/Instagram: '<id>_<id>_<id>_n.jpg' (sin fecha alguna).
_FACEBOOK_NAME = re.compile(r"_n\.(jpe?g|png|webp)$", re.I)

# Firmas de escrituras en lote vistas en VARIOS años de esta colección: la
# misma hora exacta reaparece con fechas distintas (p.ej. 18:36:52 en
# 2018/2019/2020/2023-10-20 y 2015-10-21; 12:14:52 en 2014-03-31 y
# 2015-03-15). Un EXIF sin cámara con una de estas horas es artefacto
# aunque en su carpeta quede un solo archivo con ella.
_ARTIFACT_TIMES = frozenset({
    "18:36:52", "18:43:24", "18:44:55", "12:14:52",
})


def is_artifact_stamp(moment: datetime) -> bool:
    """True si la hora EXIF coincide con una firma de lote conocida."""
    return moment.strftime("%H:%M:%S") in _ARTIFACT_TIMES

# Tipo real (FileType de exiftool) esperado para cada extensión. Si no
# coinciden, exiftool se niega a escribir y hay que corregir la extensión.
_EXPECTED_FILETYPE = {
    ".jpg": {"JPEG"}, ".jpeg": {"JPEG"}, ".png": {"PNG"},
    ".heic": {"HEIC", "HEIF"}, ".webp": {"WEBP", "Extended WEBP"}, ".mp4": {"MP4"},
    ".mov": {"MOV"}, ".avi": {"AVI"}, ".mkv": {"MKV"},
}
# Extensión correcta para cada FileType real (para poder corregirla).
_EXT_FOR_FILETYPE = {
    "JPEG": ".jpg", "PNG": ".png", "HEIC": ".heic", "HEIF": ".heic",
    "WEBP": ".webp", "Extended WEBP": ".webp", "MP4": ".mp4", "MOV": ".mov",
    "AVI": ".avi", "MKV": ".mkv",
}


def correct_extension(name: str, filetype: str) -> str | None:
    """Extensión que debería tener el archivo, o None si ya es correcta."""
    expected = _EXPECTED_FILETYPE.get(Path(name).suffix.lower())
    if expected and filetype and filetype not in expected:
        return _EXT_FOR_FILETYPE.get(filetype)
    return None


@dataclass
class AuditRow:
    """Resultado de auditar un archivo (una fila del CSV)."""

    name: str
    pattern: str          # patrón de nombre detectado
    name_date: str        # fecha derivada del nombre ('' si no hay)
    meta_date: str        # DateTimeOriginal o CreateDate ('' si no hay)
    file_date: str        # FileModifyDate (referencia, poco confiable)
    status: str           # OK / HORA_DISTINTA / FECHA_DISTINTA / ...
    suggestion: str       # acción recomendada
    evidence: str = ""    # señales para decidir en conflictos


@dataclass
class Evidence:
    """Señales del patrón de toma para juzgar un EXIF en conflicto.

    Los nombres puestos a mano "a ojo" hacen que anterior/posterior no baste:
    hace falta evidencia de si el EXIF es una captura real o un artefacto.
    """

    camera: str           # 'Make Model' si el EXIF trae cámara, '' si no
    batch_count: int      # cuántos archivos comparten este EXIF exacto
    session_count: int    # cuántos otros EXIF de la carpeta caen a ±1 h

    def is_artifact(self) -> bool:
        """EXIF escrito en lote: mismo segundo en 3+ archivos y sin cámara."""
        return not self.camera and self.batch_count >= 3

    def looks_real(self) -> bool:
        """EXIF con pinta de captura: trae cámara o encaja en una sesión."""
        return bool(self.camera) or self.session_count >= 2

    def describe(self) -> str:
        parts = [f"cámara:{self.camera}" if self.camera else "sin cámara"]
        if self.batch_count >= 2:
            parts.append(f"lote×{self.batch_count}")
        if self.session_count:
            parts.append(f"sesión:{self.session_count}±1h")
        return "; ".join(parts)


def parse_name_date(name: str) -> tuple[str, datetime | None, str]:
    """Devuelve (patrón, fecha, precisión) según el nombre del archivo."""
    for label, regex, precision in _PATTERNS:
        match = regex.match(name)
        if not match:
            continue
        try:
            if label == "facebook-epoch":
                digits = match.group(1)
                divisor = 1000 if len(digits) == 13 else 100
                return label, datetime.fromtimestamp(int(digits) / divisor), precision
            if label in ("epoch", "photostudio"):
                stamp = datetime.fromtimestamp(int(match.group(1)) / 1000)
                if not 2002 <= stamp.year <= 2035:
                    return label, None, precision
                return label, stamp, precision
            if label == "twitter":
                # Snowflake: milisegundos desde el epoch de Twitter (2010-11-04).
                stamp = datetime.fromtimestamp(
                    ((int(match.group(1)) >> 22) + 1288834974657) / 1000)
                if not 2007 <= stamp.year <= 2035:
                    return label, None, precision
                return label, stamp, precision
            if label == "12h":
                day, hour, minute, second, half = match.groups()
                hour = int(hour) % 12 + (12 if half.lower() == "pm" else 0)
                base = datetime.strptime(day, "%Y%m%d")
                return label, base.replace(hour=hour, minute=int(minute),
                                           second=int(second)), precision
            if label == "pixiz":
                return label, datetime.strptime("".join(match.groups()),
                                                "%d%m%Y%H%M%S"), precision
            if label == "chatgpt":
                return label, datetime.strptime(" ".join(match.groups()),
                                                "%b %d %Y %I %M %S %p"), precision
            digits = "".join(match.groups())
            fmt = "%Y%m%d%H%M%S" if precision == "segundos" else "%Y%m%d"
            return label, datetime.strptime(digits[:14], fmt), precision
        except (ValueError, OSError, OverflowError):
            return label, None, precision
    if _FACEBOOK_NAME.search(name):
        return "facebook", None, "día"
    return "sin-patrón", None, "día"


def _parse_meta(value: str | None) -> datetime | None:
    """Convierte una fecha de exiftool; ignora vacíos y '0000:...'."""
    if not value or value.startswith("0000"):
        return None
    try:
        return datetime.strptime(value.strip()[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def primary_meta_date(meta: dict) -> datetime | None:
    """Fecha principal de un registro de read_metadata (EXIF primero)."""
    return (_parse_meta(meta.get("DateTimeOriginal"))
            or _parse_meta(meta.get("CreateDate")))


def read_metadata(folder: Path, settings: Settings) -> list[dict]:
    """Lee las fechas de todos los archivos de la carpeta en un pase de exiftool."""
    # Sin '-fast2': HEIC guarda los metadatos al final del archivo y el modo
    # rápido no llega hasta ahí (daría falsos SIN_METADATOS).
    command = [settings.exiftool_binary, "-j", "-q",
               "-d", "%Y-%m-%d %H:%M:%S",
               "-FileName", "-FileType", "-DateTimeOriginal", "-CreateDate",
               "-FileModifyDate", "-Make", "-Model", str(folder)]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if not result.stdout.strip():
        raise DependencyError(f"exiftool no devolvió datos: {result.stderr.strip()}")
    return json.loads(result.stdout)


def gather_evidence(meta: dict, all_meta_dates: list[datetime]) -> Evidence:
    """Reúne las señales de patrón de toma para el EXIF de un archivo."""
    meta_dt = primary_meta_date(meta)
    # exiftool puede devolver Make/Model numéricos en el JSON: forzar str.
    camera = " ".join(str(part) for part in (meta.get("Make"), meta.get("Model"))
                      if part not in (None, "")).strip()
    batch = session = 0
    if meta_dt is not None:
        for other in all_meta_dates:
            seconds = abs((other - meta_dt).total_seconds())
            if seconds == 0:
                batch += 1
            elif seconds <= 3600:
                session += 1
    return Evidence(camera=camera, batch_count=batch, session_count=session)


def _classify(name: str, meta: dict, expected_year: int | None,
              tolerance: int, evidence: Evidence) -> AuditRow:
    """Compara la fecha del nombre con los metadatos y decide el estado."""
    pattern, name_dt, precision = parse_name_date(name)
    meta_dt = primary_meta_date(meta)
    row = AuditRow(name=name, pattern=pattern,
                   name_date=str(name_dt or ""), meta_date=str(meta_dt or ""),
                   file_date=meta.get("FileModifyDate", ""), status="",
                   suggestion="", evidence=evidence.describe() if meta_dt else "")
    if name_dt is None:
        row.status = "SIN_FECHA_NOMBRE"
        if meta_dt is None:
            row.suggestion = "revisar a mano (sin fecha en nombre ni metadatos)"
        elif is_artifact_stamp(meta_dt) and not evidence.camera:
            row.suggestion = "revisar a mano: EXIF con firma de lote conocida"
        elif evidence.batch_count >= 2 and not evidence.camera:
            row.suggestion = "revisar a mano: EXIF repetido en lote (no confiable)"
        else:
            row.suggestion = "fix-names: renombrar usando metadatos"
    elif meta_dt is None:
        row.status = "SIN_METADATOS"
        row.suggestion = "embed-date (escribir fecha del nombre en EXIF)"
    elif precision == "segundos" and abs((meta_dt - name_dt).total_seconds()) <= tolerance:
        row.status = "OK"
    elif meta_dt.date() == name_dt.date():
        row.status = "OK" if precision == "día" else "HORA_DISTINTA"
        if row.status == "HORA_DISTINTA":
            row.suggestion = "revisar cuál hora es la correcta"
    else:
        row.status = "FECHA_DISTINTA"
        # Anterior/posterior no basta por sí solo: hay nombres puestos a mano
        # "a ojo". Se decide con la evidencia del patrón de toma; sin
        # evidencia clara, el caso queda para revisión manual.
        if meta_dt.date() > name_dt.date():
            # Sin cámara, un EXIF posterior es de guardado/copia y embed-date
            # lo sobreescribe; con cámara podría ser la captura real (nombres
            # estimados a mano) y NUNCA se pisa automáticamente.
            if evidence.camera:
                row.suggestion = ("REVISAR: EXIF de cámara posterior al nombre; "
                                  "¿el nombre fue estimado a mano?")
            else:
                row.suggestion = ("embed-date: el nombre manda "
                                  "(EXIF posterior sin cámara)")
        else:
            if evidence.camera:
                row.suggestion = "fix-names: el EXIF manda (captura de cámara)"
            else:
                row.suggestion = "revisar a mano: sin evidencia clara"
    # Extensión que no corresponde al formato real: exiftool no puede
    # escribir ahí, así que es lo primero que hay que arreglar.
    fixed_ext = correct_extension(name, meta.get("FileType", ""))
    if fixed_ext:
        row.status = "EXTENSIÓN_INCORRECTA"
        row.suggestion = f"fix-names: corregir extensión a {fixed_ext}"
    # El año del nombre manda para detectar archivos en la carpeta equivocada.
    # Sin fecha en el nombre, el año del EXIF solo cuenta si trae cámara: un
    # EXIF de lote diría 'mover' a un año que no es de nadie.
    year = name_dt.year if name_dt else (
        meta_dt.year if meta_dt and evidence.camera else None)
    if expected_year and year and year != expected_year:
        row.status = "AÑO_INTRUSO"
        row.suggestion = f"mover a la carpeta {year}"
    return row


def audit_folder(folder: Path, settings: Settings,
                 expected_year: int | None) -> list[AuditRow]:
    """Audita todos los archivos de la carpeta (no recursivo, solo lectura)."""
    known = set(settings.image_extensions) | set(settings.video_extensions) \
        | set(settings.extra_audit_extensions)
    metas = [meta for meta in read_metadata(folder, settings)
             if Path(meta.get("FileName", "")).suffix.lower() in known]
    all_meta_dates = [dt for meta in metas
                      if (dt := primary_meta_date(meta)) is not None]
    ignored = _read_ignore_list(folder / settings.audit_ignore_name)
    rows = []
    for meta in metas:
        evidence = gather_evidence(meta, all_meta_dates)
        row = _classify(meta.get("FileName", ""), meta, expected_year,
                        settings.audit_tolerance_seconds, evidence)
        if row.name in ignored:
            row.status = "IGNORADO"
            row.suggestion = "excluido por decisión del usuario (ignore list)"
        rows.append(row)
    return sorted(rows, key=lambda row: (row.status, row.name))


def _read_ignore_list(path: Path) -> set[str]:
    """Nombres que el usuario decidió dejar tal cual (uno por línea)."""
    if not path.is_file():
        return set()
    lines = path.read_text(encoding="utf-8").splitlines()
    return {line.strip() for line in lines
            if line.strip() and not line.startswith("#")}


def write_audit_csv(rows: list[AuditRow], destination: Path) -> None:
    """Escribe el detalle por archivo, ordenado por estado."""
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["archivo", "patrón", "fecha_nombre", "fecha_metadatos",
                         "fecha_archivo", "estado", "sugerencia", "evidencia"])
        for row in rows:
            writer.writerow([row.name, row.pattern, row.name_date, row.meta_date,
                             row.file_date, row.status, row.suggestion,
                             row.evidence])


def summarize(rows: list[AuditRow]) -> Counter:
    """Cuenta archivos por estado para el resumen del log."""
    return Counter(row.status for row in rows)
