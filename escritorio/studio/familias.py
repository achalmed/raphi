"""Las familias de Raphi Studio: cada operación del motor cae en una, leída de su ficha (sin Qt, se prueba sola).

La web agrupa por categoría (Organizar, Convertir…); el escritorio, por el tipo de archivo con que trabaja la persona:
Documentos · PDF · Imágenes · Audio y video · Archivos. Una operación nueva cae sola en su familia por sus extensiones
y su tipo de entrada; solo las que no se pueden leer así van en `POR_ID`.
"""
from __future__ import annotations

# (id, nombre, para qué, icono de gui_comun.diseno)
FAMILIAS = (
    ("documentos", "Documentos", "Word, Excel, PowerPoint y OpenDocument: a PDF, entre ellos y a Markdown", "documento"),
    ("pdf", "PDF", "Unir, dividir, comprimir, OCR, sellos, foliado, firmas y seguridad", "pdf"),
    ("imagenes", "Imágenes", "Convertir, redimensionar, recortar, comprimir y ordenar fotos por fecha", "imagen"),
    ("audio_video", "Audio y video", "Convertir, recortar, descargar, transcribir y subtítulos", "audio"),
    ("archivos", "Archivos", "Comprimir, extraer y quitar metadatos de cualquier archivo", "archivo"),
)

IMG = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".avif", ".tif", ".tiff", ".bmp", ".gif", ".svg"}
MEDIOS = {".mp3", ".m4a", ".aac", ".flac", ".opus", ".ogg", ".wav", ".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v",
          ".srt", ".vtt"}

# Las que su ficha no deja leer (sin extensiones, o con entradas mezcladas)
POR_ID = {
    "descargar": "audio_video", "auditar_fechas_fotos": "imagenes", "ordenar_fotos_por_fecha": "imagenes",
    "imagenes_a_pdf": "documentos", "inventario_paginas": "pdf", "estampar_imagen": "pdf",
}

# El icono de cada operación: el de su familia, salvo estas
ICONO_POR_ID = {"descargar": "descarga", "transcribir": "texto", "ajustar_subtitulos": "subtitulos",
                "convertir_subtitulos": "subtitulos", "convertir_video": "video", "comprimir_video": "video",
                "recortar_medio": "video", "auditar_fechas_fotos": "imagen", "ordenar_fotos_por_fecha": "carpeta"}


def familia_de(ficha: dict) -> str:
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
    return next(icono for id_, _n, _d, icono in FAMILIAS if id_ == familia_de(ficha))


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
        return carpetas if ficha["id"] in ("auditar_fechas_fotos", "ordenar_fotos_por_fecha") else not carpetas
    return all(Path(r).suffix.lower() in ext for r in rutas)
