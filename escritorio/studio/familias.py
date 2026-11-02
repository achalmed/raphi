"""Las familias de Raphi Studio: cada operación del motor cae en una, leída de su ficha (sin Qt, se prueba sola).

La web agrupa por categoría (Organizar, Convertir…); el escritorio, por el tipo de archivo con que trabaja la persona:
Documentos · PDF · Imágenes · Audio y video · Archivos, y Recetas. Una operación nueva cae sola en su familia por sus
extensiones y su tipo de entrada; solo las que no se pueden leer así van en `POR_ID`. Es el único archivo del studio
que nombra operaciones (lo vigila `tests/test_studio.py`).
"""
from __future__ import annotations

# (id, nombre, para qué, icono del tema)
FAMILIAS = (
    ("documentos", "Documentos", "Word, Excel, PowerPoint y OpenDocument: a PDF, entre ellos y a Markdown", "x-office-document"),
    ("pdf", "PDF", "Unir, dividir, comprimir, OCR, sellos, foliado, firmas y seguridad", "application-pdf"),
    ("imagenes", "Imágenes", "Convertir, redimensionar, recortar, comprimir y ordenar fotos por fecha", "image-x-generic"),
    ("audio_video", "Audio y video", "Convertir, recortar, descargar, transcribir y subtítulos", "video-x-generic"),
    ("archivos", "Archivos", "Comprimir, extraer y quitar metadatos de cualquier archivo", "package-x-generic"),
    ("recetas", "Recetas", "Varias herramientas, una tras otra, con sus opciones guardadas", "view-list-tree"),
)
NOMBRES = {id_: nombre for id_, nombre, _p, _i in FAMILIAS}
ICONOS = {id_: icono for id_, _n, _p, icono in FAMILIAS}

IMG = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".avif", ".tif", ".tiff", ".bmp", ".gif", ".svg"}
MEDIOS = {".mp3", ".m4a", ".aac", ".flac", ".opus", ".ogg", ".wav", ".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v",
          ".srt", ".vtt"}

# Las que su ficha no deja leer (sin extensiones, o con entradas mezcladas)
POR_ID = {
    "descargar": "audio_video", "auditar_fechas_fotos": "imagenes", "ordenar_fotos_por_fecha": "imagenes",
    "imagenes_a_pdf": "documentos", "inventario_paginas": "pdf", "estampar_imagen": "pdf",
}
CON_CARPETAS = {"auditar_fechas_fotos", "ordenar_fotos_por_fecha"}

# El icono de cada operación: el de su familia, salvo estas
ICONO_POR_ID = {"descargar": "download", "transcribir": "text-x-generic", "ajustar_subtitulos": "media-subtitle",
                "convertir_subtitulos": "media-subtitle", "convertir_video": "video-x-generic", "comprimir_video": "video-x-generic",
                "recortar_medio": "edit-cut", "auditar_fechas_fotos": "image-x-generic", "ordenar_fotos_por_fecha": "folder-images"}


def nombre_de(familia: str) -> str:
    return NOMBRES.get(familia, familia.capitalize())


def icono_familia(familia: str) -> str:
    return ICONOS.get(familia, "application-x-executable")


def familia_de(ficha: dict) -> str:
    if ficha.get("es_receta"):
        return "recetas"
    if ficha["id"] in POR_ID:
        return POR_ID[ficha["id"]]
    if ficha["entrada"] in ("pdf", "pdfs"):
        return "pdf"
    if ficha["entrada"] == "documentos":
        return "documentos"
    ext = {e.lower() for e in ficha.get("extensiones", ())}
    if ext and ext <= IMG:
        return "imagenes"
    if ext & MEDIOS and ext <= IMG | MEDIOS:          # un video también acepta GIF: sigue siendo audio y video
        return "audio_video"
    return "archivos"


def icono_de(ficha: dict) -> str:
    if ficha["id"] in ICONO_POR_ID:
        return ICONO_POR_ID[ficha["id"]]
    return icono_familia(familia_de(ficha))


def trabaja_con_carpetas(ficha: dict) -> bool:
    return ficha["id"] in CON_CARPETAS


def acepta(ficha: dict, rutas: list[str]) -> bool:
    """¿Sirve esta operación para estos archivos? (lo soltado sobre la ventana)."""
    from pathlib import Path
    if not rutas or ficha["minimo_entradas"] == 0 or ficha["entrada"] == "ninguna":
        return False
    if len(rutas) < ficha["minimo_entradas"]:
        return False
    ext = {e.lower() for e in ficha.get("extensiones", ())}
    if not ext:                                         # trabaja con carpetas o con cualquier archivo
        carpetas = all(Path(r).is_dir() for r in rutas)
        return carpetas if trabaja_con_carpetas(ficha) else not carpetas
    return all(Path(r).suffix.lower() in ext for r in rutas)
