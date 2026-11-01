"""Configuración central de photo-metadata-suite.

Todo valor ajustable vive aquí. Edita este archivo para cambiar el
comportamiento por defecto sin tocar la lógica en `lib/`. Cualquier campo
puede además sobreescribirse por CLI (ver `lib/cli.py`).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

APP_NAME = "photo-metadata-suite"
VERSION = "2.0.0"

# --- Códigos de salida del proyecto (126/127 los reserva el shell) ---
EXIT_OK = 0
EXIT_GENERAL = 1
EXIT_USAGE = 2
EXIT_NOT_FOUND = 3
EXIT_PERMISSION = 4
EXIT_DEPENDENCY = 5


@dataclass
class Settings:
    """Parámetros de ejecución. Instancia picklable para multiprocessing.

    Las fracciones de recorte se expresan en 0..1 relativas al tamaño de
    cada imagen, de modo que funcionan igual en cualquier resolución.
    """

    # --- Región de análisis: DÓNDE se lee la marca (esquina, franja...) ---
    crop_left_frac: float = 0.0
    crop_top_frac: float = 0.0
    crop_width_frac: float = 0.40
    crop_height_frac: float = 0.075
    upscale_factor: int = 4  # ampliar el recorte ayuda al OCR

    # --- OCR: barrido de umbrales y opciones de tesseract ---
    bright_thresholds: list = field(  # texto blanco sobre fondo oscuro
        default_factory=lambda: [140, 160, 180, 200, 220, 235])
    dark_thresholds: list = field(  # respaldo: contorno oscuro (sobreexpuestas)
        default_factory=lambda: [70, 100, 130, 160])
    tesseract_psms: list = field(default_factory=lambda: [7, 6])
    tesseract_whitelist: str = "0123456789-: "
    tesseract_lang: Optional[str] = None

    # --- Interpretación y validación del texto reconocido ---
    timestamp_regex: str = (
        r"(\d{4})-(\d{2})-(\d{2})[^\d]*(\d{2})[^\d]*(\d{2})[^\d]*(\d{2})")
    year_min: int = 2015
    year_max: int = 2035
    confident_min_votes: int = 3  # votos mínimos para marcar "confident"

    # --- Archivos que se consideran fotos ---
    image_extensions: tuple = (".jpg", ".jpeg", ".png")

    # Qué tipo de medios procesar: "all" | "images" | "videos".
    media_filter: str = "all"

    # --- Metadatos (exiftool): escribir la fecha de captura desde el nombre ---
    exiftool_binary: str = "exiftool"
    # Convierte 'AAAAMMDD_HHMMSS[_N].ext' -> 'AAAA:MM:DD HH:MM:SS' (formato EXIF).
    filename_date_expr: str = (
        r"${filename;s/(\d{8})_(\d{6}).*/$1$2/;"
        r"s/(\d{4})(\d\d)(\d\d)(\d\d)(\d\d)(\d\d)/$1:$2:$3 $4:$5:$6/}")
    # Fijar además la fecha del sistema (FileModifyDate) desde el nombre: sirve
    # de respaldo para formatos sin metadatos escribibles (p.ej. M2TS con
    # extensión .mp4) y deja el mtime coherente con la fecha de captura.
    set_file_modify_date: bool = True
    # Escribir la fecha SOLO donde falten DateTimeOriginal y CreateDate.
    # Evita pisar el EXIF de las fotos que ya están correctas.
    embed_only_missing: bool = True
    # Modo fotos escaneadas (--trust-name): el nombre manda SIEMPRE, incluso
    # sobre EXIF con cámara (que ahí es el escáner/celular que digitalizó,
    # con la fecha del escaneo, no la de la foto histórica).
    trust_name: bool = False
    # Además, sobreescribir cuando el EXIF existente sea POSTERIOR al día del
    # nombre: una foto no puede capturarse después de recibirse/nombrarse, así
    # que ese EXIF es un artefacto (copias, guardados en lote). Un EXIF
    # anterior al nombre se respeta siempre (podría ser la captura real).
    overwrite_later_exif: bool = True

    image_date_tags: tuple = ("AllDates",)  # DateTimeOriginal + CreateDate + ModifyDate
    # Los videos de la cámara guardan la fecha en QuickTime Y en varios bloques
    # XMP; digiKam suele leer XMP-exif:DateTimeOriginal, así que hay que fijar
    # todos para que la fecha real quede consistente en cualquier lector.
    video_date_tags: tuple = (
        "QuickTime:CreateDate", "QuickTime:ModifyDate",
        "TrackCreateDate", "TrackModifyDate",
        "MediaCreateDate", "MediaModifyDate",
        "XMP-exif:DateTimeOriginal", "XMP-photoshop:DateCreated",
        "XMP-tiff:DateTime", "XMP-xmp:CreateDate",
        "XMP-xmp:ModifyDate", "XMP-xmp:MetadataDate")

    # --- Videos: se extrae un fotograma y se le aplica el MISMO OCR ---
    video_extensions: tuple = (".mp4", ".mov", ".avi", ".mkv")
    ffmpeg_binary: str = "ffmpeg"
    # Segundos a probar para sacar el fotograma; el primero legible gana. El
    # fotograma en "0" contiene la hora de INICIO de la grabación (la que
    # queremos); los siguientes son respaldo si el primero es negro/transición.
    ffmpeg_frame_times: list = field(default_factory=lambda: ["0", "1", "2"])

    # --- Ejecución ---
    workers: int = 0  # 0 => usar todos los núcleos
    omp_thread_limit: str = "1"  # evita que tesseract sature los núcleos
    progress_every: int = 20
    limit: int = 0  # 0 => sin límite (útil para pruebas rápidas)

    # --- Auditoría de fechas (audit-dates): nombre vs metadatos ---
    # Tolerancia en segundos entre la fecha del nombre y la EXIF para dar OK
    # (cámaras y relojes suelen diferir 1-2 s al guardar).
    audit_tolerance_seconds: int = 60
    # Extensiones adicionales que la auditoría revisa aunque el renombrador
    # no las procese (fotos de iPhone y stickers/exportados de WhatsApp).
    extra_audit_extensions: tuple = (".heic", ".webp")

    # --- Nombres de salida (se crean dentro de la carpeta objetivo) ---
    audit_csv_name: str = "date_audit.csv"
    fix_log_name: str = "_fix_log.csv"
    # Lista de excepciones por carpeta: archivos que el usuario decidió dejar
    # tal cual (p.ej. relojes reiniciados con fecha imposible pero real
    # desconocida). Un nombre por línea; '#' comenta.
    audit_ignore_name: str = "date_audit_ignore.txt"
    # Base de datos de digiKam (sync-digikam la lee EN COPIA, jamás la toca).
    digikam_db_name: str = "digikam4.db"
    # fix-names: renombrar desde el EXIF cuando el nombre no trae fecha o
    # cuando el EXIF es anterior al nombre (el nombre vino de una exportación).
    rename_from_metadata: bool = True
    plan_csv_name: str = "rename_plan.csv"
    analysis_json_name: str = "analysis.json"
    log_csv_name: str = "_rename_log.csv"
    undo_script_name: str = "_undo_rename.sh"
    temp_prefix: str = ".__ren_tmp_"
    montage_rows_per_image: int = 28


def default_settings() -> Settings:
    """Devuelve la configuración por defecto (punto único de creación)."""
    return Settings()
