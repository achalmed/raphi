"""Los menús del clic derecho en Dolphin (KDE): «Raphi ▸ Abrir en Raphi · Comprimir PDF · PDF a Word · A JPG · A PDF ·
Quitar metadatos…». Las acciones rápidas corren la CLI junto al original y avisan al terminar (`raphi accion`); «Abrir
en Raphi» manda los archivos a la ventana.

Los archivos van a `$XDG_DATA_HOME/kio/servicemenus/raphi-<familia>.desktop` y deben ser ejecutables (Plasma 6 lo
exige); quitarlos borra solo los que llevan la marca de Raphi.
"""
from __future__ import annotations

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
LANZADOR = RAIZ / "run.sh"

TIPOS = ("application/pdf", "image/jpeg", "image/png", "image/webp", "image/heic", "image/heif", "image/avif", "image/tiff",
         "video/mp4", "video/quicktime", "video/x-matroska", "video/webm", "audio/mpeg", "audio/mp4", "audio/flac",
         "audio/ogg", "audio/x-wav", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
         "application/vnd.openxmlformats-officedocument.presentationml.presentation",
         "application/vnd.oasis.opendocument.text", "application/msword", "application/rtf", "application/zip")

# (id, nombre, tipos a los que se ofrece, orden)
ACCIONES = (
    ("abrir", "Abrir en Raphi", ("all/allfiles",), "escritorio"),
    ("comprimir", "Comprimir PDF (hasta 10 MB)", ("application/pdf",), "accion comprimir --hasta 10 --umbral 0"),
    ("ocr", "Hacer buscable (OCR)", ("application/pdf",), "accion ocr"),
    ("word", "PDF a Word", ("application/pdf",), "accion pdf_a_word"),
    ("foliar", "Foliar", ("application/pdf",), "accion foliar"),
    ("a_pdf", "Convertir a PDF", TIPOS[17:23], "accion a_pdf"),
    ("img_pdf", "Imágenes a un PDF", TIPOS[1:8], "accion imagenes_a_pdf"),
    ("jpg", "Convertir a JPG", TIPOS[1:8], "accion convertir_imagen --formato jpg"),
    ("mp4", "Convertir a MP4", TIPOS[8:12], "accion convertir_video --formato mp4"),
    ("mp3", "Extraer el audio (MP3)", TIPOS[8:17], "accion convertir_audio --formato mp3"),
    ("limpiar", "Quitar metadatos", ("all/allfiles",), "accion quitar_metadatos_archivo"),
)


MARCA = "# Generado por Raphi escritorio (escritorio/dolphin.py); se quita desde Raphi → Sistema."


def carpeta_menus() -> Path:
    base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "kio" / "servicemenus"


def grupos() -> dict[str, list[tuple[str, str, str]]]:
    """En KDE el tipo de archivo se declara por archivo de menú, no por acción: un archivo por familia de tipos
    (raphi-<familia>.desktop), todos en el mismo submenú «Raphi», que Dolphin junta."""
    salida: dict[tuple[str, ...], list[tuple[str, str, str]]] = {}
    for ident, nombre, tipos, orden in ACCIONES:
        salida.setdefault(tuple(tipos), []).append((ident, nombre, orden))
    familia = {("all/allfiles",): "todo", ("application/pdf",): "pdf", tuple(TIPOS[1:8]): "imagenes",
               tuple(TIPOS[8:12]): "video", tuple(TIPOS[8:17]): "audio-video", tuple(TIPOS[17:23]): "oficina"}
    return {familia.get(k, f"grupo{i}"): (k, v) for i, (k, v) in enumerate(salida.items())}


def contenido(tipos: tuple[str, ...], acciones: list[tuple[str, str, str]]) -> str:
    lineas = [MARCA, "[Desktop Entry]", "Type=Service", f"MimeType={';'.join(tipos)};", "X-KDE-Submenu=Raphi",
              f"Actions={';'.join(a for a, *_ in acciones)};", ""]
    for ident, nombre, orden in acciones:
        lineas += [f"[Desktop Action {ident}]", f"Name={nombre}", "Icon=document-edit", f"Exec={LANZADOR} {orden} %F", ""]
    return "\n".join(lineas)


def instalados() -> list[Path]:
    c = carpeta_menus()
    return [p for p in c.glob("raphi-*.desktop") if MARCA in p.read_text(encoding="utf-8", errors="ignore")] if c.is_dir() else []


def hay() -> bool:
    return bool(instalados())


def instalar(si: bool) -> bool:
    for p in instalados():
        p.unlink()
    if si:
        carpeta = carpeta_menus()
        carpeta.mkdir(parents=True, exist_ok=True)
        for familia, (tipos, acciones) in grupos().items():
            ruta = carpeta / f"raphi-{familia}.desktop"
            ruta.write_text(contenido(tipos, acciones), encoding="utf-8")
            ruta.chmod(0o755)                       # Plasma 6 solo muestra menús ejecutables
    return hay()
