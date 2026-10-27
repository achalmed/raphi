"""Documentos de oficina: a PDF (LibreOffice aislado), entre formatos (Office ↔ ODF), imágenes a PDF y a Markdown.

A Markdown usa `docflow` (sus parsers propios de pptx y xlsx) si está: dentro de este repo, `backends/docflow`; si
no, el de PATH. Si no hay docflow, la operación no aparece como disponible.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from raphi.motor.base import ErrorOperacion, Parametro, Resultado, disponible, operacion
from raphi.motor.utiles import correr, soffice

OFIMATICA = (".doc", ".docx", ".dotx", ".odt", ".rtf", ".txt", ".xls", ".xlsx", ".ods", ".csv", ".ppt", ".pptx",
             ".odp", ".html", ".htm", ".epub")
IMAGENES = (".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".avif", ".tif", ".tiff", ".bmp", ".gif")

# formato de destino → (extensión, filtro de LibreOffice)
DESTINOS = {"docx": ("docx", "docx:MS Word 2007 XML"), "odt": ("odt", "odt"), "xlsx": ("xlsx", "xlsx:Calc MS Excel 2007 XML"),
            "ods": ("ods", "ods"), "pptx": ("pptx", "pptx:Impress MS PowerPoint 2007 XML"), "odp": ("odp", "odp"),
            "rtf": ("rtf", "rtf"), "txt": ("txt", "txt:Text"), "html": ("html", "html")}
# LibreOffice convierte dentro de una familia: un texto no se vuelve hoja de cálculo ni presentación.
FAMILIAS = {
    "texto": ((".doc", ".docx", ".dotx", ".odt", ".rtf", ".txt", ".html", ".htm", ".epub"), ("docx", "odt", "rtf", "txt", "html")),
    "hoja de cálculo": ((".xls", ".xlsx", ".ods", ".csv"), ("xlsx", "ods", "html")),
    "presentación": ((".ppt", ".pptx", ".odp"), ("pptx", "odp")),
}


def destinos_de(extension: str) -> tuple[str, tuple[str, ...]]:
    """La familia de una extensión de oficina y los formatos a los que se convierte (sin el suyo)."""
    extension = extension.lower()
    for familia, (extensiones, destinos) in FAMILIAS.items():
        if extension in extensiones:
            return familia, tuple(d for d in destinos if f".{d}" != extension)
    return "", ()


@operacion("a_pdf", "Convertir", "Documento a PDF", "Word, Excel, PowerPoint, LibreOffice, RTF, texto o HTML a PDF.",
           entrada="documentos", extensiones=OFIMATICA, sufijo="pdf", requiere=("soffice",),
           palabras=("word a pdf", "excel a pdf", "convertir", "docx", "office"))
def a_pdf(ctx):
    destino = ctx.salida(extension=".pdf", nombre=ctx.entrada.stem)
    if ctx.simular:
        return Resultado(plan=[f"{ctx.entrada.name} → {destino.name}"])
    tmp = ctx.carpeta_temporal()
    hecho = soffice(ctx.entrada, "pdf", tmp)
    shutil.move(str(hecho), destino)
    return Resultado([destino])


@operacion("ofimatica", "Convertir", "Entre formatos de oficina", "Office ↔ LibreOffice (docx ↔ odt, xlsx ↔ ods, pptx ↔ odp) y más.",
           entrada="documentos", extensiones=OFIMATICA, sufijo="convertido", requiere=("soffice",),
           parametros=(Parametro("formato", "A", "opcion", "odt", opciones=tuple(DESTINOS)),),
           palabras=("odt", "ods", "odp", "docx", "xlsx", "pptx", "libreoffice"))
def ofimatica(ctx):
    ext, filtro = DESTINOS[ctx.p("formato")]
    if ctx.entrada.suffix.lower() == f".{ext}":
        raise ErrorOperacion(f"{ctx.entrada.name} ya es .{ext}.")
    familia, destinos = destinos_de(ctx.entrada.suffix)
    if ext not in destinos:
        raise ErrorOperacion(f"{ctx.entrada.name} es {familia or 'otro formato'}: se convierte a {', '.join(destinos) or 'PDF'}, no a .{ext}.")
    destino = ctx.salida(extension=f".{ext}", nombre=ctx.entrada.stem)
    if ctx.simular:
        return Resultado(plan=[f"{ctx.entrada.name} → {destino.name}"])
    hecho = soffice(ctx.entrada, filtro, ctx.carpeta_temporal())
    shutil.move(str(hecho), destino)
    return Resultado([destino])


@operacion("imagenes_a_pdf", "Convertir", "Imágenes a PDF",
           "Junta fotos o escaneos (también HEIC del celular) en un PDF, una por página, en el orden dado.",
           entrada="imagenes", lote=False, extensiones=IMAGENES, sufijo="imagenes", requiere=("py:PIL",),
           parametros=(Parametro("nombre", "Nombre del archivo", "texto", "imagenes"),
                       Parametro("papel", "Página", "opcion", "imagen",
                                 opciones=(("imagen", "Del tamaño de cada imagen"), ("A4", "A4"), ("carta", "Carta"))),
                       Parametro("ppp", "Resolución (ppp)", "entero", 150, minimo=72, maximo=600),
                       Parametro("calidad", "Calidad JPG", "entero", 85, minimo=30, maximo=100)),
           palabras=("fotos", "escanear", "jpg a pdf", "png a pdf", "heic", "celular"))
def imagenes_a_pdf(ctx):
    from PIL import Image, ImageOps
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass
    destino = ctx.salida(nombre=ctx.p("nombre") or "imagenes", extension=".pdf")
    if ctx.simular:
        return Resultado(plan=[f"{len(ctx.entradas)} imágenes → {destino.name}"])
    papeles = {"A4": (8.27, 11.69), "carta": (8.5, 11.0)}
    paginas = []
    for i, ruta in enumerate(ctx.entradas):
        ctx.avisar(i / len(ctx.entradas), ruta.name)
        try:
            with Image.open(ruta) as img:
                img = ImageOps.exif_transpose(img).convert("RGB")
        except OSError as e:
            raise ErrorOperacion(f"{ruta.name}: la imagen está dañada o no se puede leer.") from e
        if ctx.p("papel") in papeles:
            w, h = papeles[ctx.p("papel")]
            if img.width > img.height:
                w, h = h, w
            lienzo = Image.new("RGB", (int(w * ctx.p("ppp")), int(h * ctx.p("ppp"))), "white")
            img.thumbnail(lienzo.size)
            lienzo.paste(img, ((lienzo.width - img.width) // 2, (lienzo.height - img.height) // 2))
            img = lienzo
        paginas.append(img)
    paginas[0].save(destino, "PDF", save_all=True, append_images=paginas[1:], resolution=ctx.p("ppp"),
                    quality=ctx.p("calidad"))
    return Resultado([destino], {"paginas": len(paginas)})


def _docflow() -> str | None:
    propio = Path(__file__).resolve().parents[2] / "backends" / "docflow" / "bin" / "docflow"
    return str(propio) if propio.is_file() else shutil.which("docflow")


@operacion("a_markdown", "Convertir", "Documento a Markdown",
           "Word, PowerPoint, Excel, PDF y más a Markdown con su frontmatter (con docflow, que lee pptx y xlsx).",
           entrada="documentos", extensiones=OFIMATICA + (".pdf", ".md", ".tex"), sufijo="md",
           requiere=("pandoc",), palabras=("md", "markdown", "obsidian", "texto"))
def a_markdown(ctx):
    docflow = _docflow()
    if not docflow:
        raise ErrorOperacion("Falta docflow (backends/docflow o en PATH).")
    destino = ctx.salida(extension=".md", nombre=ctx.entrada.stem)
    if ctx.simular:
        return Resultado(plan=[f"{ctx.entrada.name} → {destino.name} (docflow to-md)"])
    tmp = ctx.carpeta_temporal()
    copia = tmp / ctx.entrada.name
    shutil.copy2(ctx.entrada, copia)
    correr([docflow, "to-md", "--quiet", str(copia)], timeout=900, mensaje="docflow no pudo convertirlo")
    hechos = [p for p in tmp.rglob("*.md") if p.is_file()]
    if not hechos:
        raise ErrorOperacion("docflow no produjo el Markdown.")
    shutil.move(str(hechos[0]), destino)
    medios = [p for p in tmp.rglob("*") if p.is_dir() and p.name.endswith(("_media", "_files", "media"))]
    for m in medios:
        shutil.move(str(m), destino.parent / m.name)
    return Resultado([destino])


def docflow_disponible() -> bool:
    return _docflow() is not None and disponible("pandoc")
