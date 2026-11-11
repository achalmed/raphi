"""Las familias y las áreas de Raphi Studio: cada operación del motor cae en una familia y en una o más áreas del
catálogo, leídas de su ficha (sin Qt, se prueba sola).

La web agrupa por categoría (Organizar, Convertir…); el escritorio, por el tipo de archivo con que trabaja la persona:
Documentos · PDF · Imágenes · Audio y video · Archivos, y Recetas. Una operación nueva cae sola en su familia por sus
extensiones y su tipo de entrada; solo las que no se pueden leer así van en `POR_ID`. Es el único archivo del studio
que nombra operaciones (lo vigila `tests/test_studio.py`).

Las áreas (reingeniería X1, `docs/reingenieria.md`) son las del catálogo: Documentos y PDF · Imágenes · Audio · Vídeo ·
Transcripción · Conversión · Procesamiento por lotes · Automatización y recetas. Una herramienta puede estar en varias
(convertir un vídeo es Vídeo y Conversión); la primera es la suya.
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

# El icono de cada operación: el de su familia, salvo estas (el catálogo de Raphi Studio y la rueda de soltar)
ICONO_POR_ID = {"descargar": "download", "transcribir": "text-x-generic", "ajustar_subtitulos": "media-subtitle",
                "convertir_subtitulos": "media-subtitle", "convertir_video": "video-x-generic", "comprimir_video": "transform-scale",
                "recortar_medio": "edit-cut", "auditar_fechas_fotos": "image-x-generic", "ordenar_fotos_por_fecha": "folder-images",
                "comprimir": "transform-scale", "comprimir_imagen": "transform-scale", "comprimir_archivos": "archive-insert",
                "extraer_archivo": "archive-extract", "recortar_imagen": "transform-crop", "fondo_imagen": "fill-color",
                "redimensionar_imagen": "image-resize-symbolic", "quitar_metadatos_archivo": "edit-clear-all",
                "quitar_metadatos": "edit-clear-all", "metadatos": "document-properties", "ocr": "document-scan",
                "tachar": "format-text-strikethrough", "nota": "knotes", "marca_agua": "insert-text", "rotar": "object-rotate-right",
                "dividir": "edit-cut", "foliar": "format-list-ordered", "sello": "document-sign", "resaltar": "draw-highlight",
                "cifrar": "document-encrypt", "firmas": "security-high", "tablas_a_excel": "x-office-spreadsheet",
                "leer_comprobante": "document-preview", "unir": "merge", "comparar": "kompare"}


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


# ======================================================================================================================
# Las áreas del catálogo (reingeniería X1)

AREAS = (
    ("documentos_pdf", "Documentos y PDF", "Ofimática, PDF: unir, dividir, comprimir, OCR, sellos, firmas y seguridad", "application-pdf"),
    ("imagenes", "Imágenes", "Convertir, redimensionar, recortar, comprimir y ordenar fotos por fecha", "image-x-generic"),
    ("audio", "Audio", "Convertir y recortar audio, descargar y transcribir", "audio-x-generic"),
    ("video", "Vídeo", "Convertir, comprimir, recortar y descargar vídeo", "video-x-generic"),
    ("transcripcion", "Transcripción", "Del audio al texto con Whisper, y los subtítulos", "audio-input-microphone"),
    ("conversion", "Conversión", "De un formato a otro: documentos, PDF, imágenes, audio, vídeo y subtítulos", "document-export"),
    ("lotes", "Procesamiento por lotes", "Las que trabajan con carpetas o reúnen muchos archivos en uno (todas aceptan varios archivos)", "folder-documents"),
    ("recetas", "Automatización y recetas", "Varias herramientas, una tras otra, con sus opciones guardadas", "view-list-tree"),
)
NOMBRES_AREA = {id_: nombre for id_, nombre, _p, _i in AREAS}
ICONOS_AREA = {id_: icono for id_, _n, _p, icono in AREAS}
AUDIO = {".mp3", ".m4a", ".aac", ".flac", ".opus", ".ogg", ".wav"}
VIDEO = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
SUBTITULOS = {".srt", ".vtt"}
# las que su ficha no deja leer del todo
TRANSCRIPCION_POR_ID = {"transcribir"}
AUDIO_Y_VIDEO_POR_ID = {"descargar"}
LOTES_POR_ID = {"inventario_paginas"} | CON_CARPETAS


def nombre_area(area: str) -> str:
    return NOMBRES_AREA.get(area, area)


def areas_de(ficha: dict) -> list[str]:
    """Las áreas de una herramienta, la suya primero."""
    if ficha.get("es_receta"):
        return ["recetas"]
    familia = familia_de(ficha)
    ext = {e.lower() for e in ficha.get("extensiones", ())}
    salida: list[str] = []

    def poner(a: str) -> None:
        if a not in salida:
            salida.append(a)

    if ficha["id"] in TRANSCRIPCION_POR_ID:
        poner("transcripcion")
    if familia in ("pdf", "documentos"):
        poner("documentos_pdf")
    elif familia == "imagenes":
        poner("imagenes")
    elif familia == "audio_video":
        if ext and ext <= SUBTITULOS:
            poner("transcripcion")
        if ficha["id"] in AUDIO_Y_VIDEO_POR_ID:
            poner("video")
            poner("audio")
        if ext & AUDIO:                                # acepta audio (y quizá vídeo, del que saca el audio)
            poner("audio")
        if ext & VIDEO:
            poner("video")
    if ficha.get("categoria") == "Convertir" or (ext and ext <= SUBTITULOS and familia == "audio_video" and "convertir" in ficha["id"]) \
            or ficha["id"].startswith("convertir_"):
        poner("conversion")
    if familia == "archivos" or ficha["id"] in LOTES_POR_ID or (not ficha.get("lote", True) and ficha.get("entrada") in ("pdfs", "imagenes")):
        poner("lotes")
    return salida or ["lotes"]


def formatos_texto(ficha: dict, tope: int = 6) -> str:
    """Los formatos que acepta, cortos: «PDF», «JPG PNG WEBP …», «carpetas», «sin archivos»."""
    if ficha.get("entrada") == "ninguna" or ficha.get("minimo_entradas", 1) == 0:
        return "sin archivos (una dirección o nada)"
    ext = ficha.get("extensiones") or []
    if not ext:
        return "carpetas" if trabaja_con_carpetas(ficha) else "cualquier archivo"
    vistos: list[str] = []
    for e in ext:
        e = e.lstrip(".").upper().replace("JPEG", "JPG")
        if e not in vistos:
            vistos.append(e)
    return " ".join(vistos[:tope]) + (" …" if len(vistos) > tope else "")
