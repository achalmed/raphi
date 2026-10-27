"""Contenido: PDF a imagen, texto, HTML y Word; extraer imágenes; OCR; qué necesita OCR; miniaturas."""
from __future__ import annotations

import shutil

from raphi.motor.base import ErrorOperacion, Parametro, Resultado, operacion, paginas_de
from raphi.motor.utiles import correr, interpretar_paginas, soffice


@operacion("pdf_a_imagen", "Convertir", "PDF a imagen", "Cada página como imagen (PNG, JPG o TIFF).",
           sufijo="imagenes", requiere=("pdftocairo",),
           parametros=(Parametro("formato", "Formato", "opcion", "png", opciones=("png", "jpg", "tiff")),
                       Parametro("ppp", "Resolución (ppp)", "entero", 150, minimo=36, maximo=1200),
                       Parametro("paginas", "Páginas (vacío = todas)", "paginas", "")),
           palabras=("png", "jpg", "jpeg", "imagen", "captura", "rasterizar"))
def pdf_a_imagen(ctx):
    total = paginas_de(ctx.entrada)
    indices = interpretar_paginas(ctx.p("paginas"), total)
    carpeta = ctx.carpeta_salida()
    if ctx.simular:
        return Resultado(plan=[f"{len(indices)} imágenes {ctx.p('formato')} a {ctx.p('ppp')} ppp → {carpeta.name}/"])
    bandera = {"png": "-png", "jpg": "-jpeg", "tiff": "-tiff"}[ctx.p("formato")]
    ancho = len(str(total))
    for i, n in enumerate(indices):
        ctx.avisar(i / len(indices), f"página {n + 1}")
        correr(["pdftocairo", bandera, "-r", str(ctx.p("ppp")), "-f", str(n + 1), "-l", str(n + 1), "-singlefile",
                str(ctx.entrada), str(carpeta / f"{ctx.entrada.stem}-{str(n + 1).zfill(ancho)}")])
    return Resultado([carpeta], {"imagenes": len(indices)})


@operacion("pdf_a_texto", "Convertir", "PDF a texto", "Extrae el texto (conservando la disposición, si se pide).",
           sufijo="texto", requiere=("pdftotext",),
           parametros=(Parametro("disposicion", "Conservar la disposición", "casilla", True),),
           palabras=("txt", "texto plano", "extraer texto"))
def pdf_a_texto(ctx):
    destino = ctx.salida(extension=".txt", nombre=ctx.entrada.stem)
    if ctx.simular:
        return Resultado(plan=[f"texto → {destino.name}"])
    correr(["pdftotext", *(["-layout"] if ctx.p("disposicion") else []), "-enc", "UTF-8", str(ctx.entrada), str(destino)])
    caracteres = len(destino.read_text(errors="ignore").strip())
    mensajes = [] if caracteres else ["El PDF no tiene capa de texto: pase antes por «OCR»."]
    return Resultado([destino], {"caracteres": caracteres}, mensajes)


@operacion("pdf_a_html", "Convertir", "PDF a HTML", "Una página web con el texto y las imágenes de cada página.",
           sufijo="html", requiere=("py:pymupdf",), palabras=("web", "html"))
def pdf_a_html(ctx):
    import pymupdf
    destino = ctx.salida(extension=".html", nombre=ctx.entrada.stem)
    if ctx.simular:
        return Resultado(plan=[f"HTML → {destino.name}"])
    with pymupdf.open(ctx.entrada) as doc:
        cuerpo = "\n".join(f'<section class="pagina" id="p{i + 1}">{p.get_text("html")}</section>' for i, p in enumerate(doc))
    destino.write_text(f'<!doctype html><html lang="es"><meta charset="utf-8"><title>{ctx.entrada.stem}</title>'
                       f'<style>.pagina{{position:relative;margin:1em auto;box-shadow:0 0 4px #999}}</style>'
                       f"<body>{cuerpo}</body></html>")
    return Resultado([destino])


@operacion("pdf_a_word", "Convertir", "PDF a Word (básico)",
           "Lo abre LibreOffice y lo guarda como .docx: sirve para recuperar el texto; el diseño puede variar.",
           sufijo="word", requiere=("soffice",), palabras=("docx", "word", "editable"))
def pdf_a_word(ctx):
    destino = ctx.salida(extension=".docx", nombre=ctx.entrada.stem)
    if ctx.simular:
        return Resultado(plan=[f"Word → {destino.name}"])
    tmp = ctx.carpeta_temporal()
    hecho = soffice(ctx.entrada, "docx:MS Word 2007 XML", tmp, filtro_entrada="writer_pdf_import")
    shutil.move(str(hecho), destino)
    return Resultado([destino], mensajes=["Conversión básica: revise el diseño."])


@operacion("extraer_imagenes", "Convertir", "Extraer imágenes", "Saca las imágenes incrustadas tal como están en el PDF.",
           sufijo="imagenes", requiere=("pdfimages",), palabras=("fotos", "imágenes", "recuperar"))
def extraer_imagenes(ctx):
    carpeta = ctx.carpeta_salida()
    if ctx.simular:
        return Resultado(plan=[f"imágenes → {carpeta.name}/"])
    correr(["pdfimages", "-all", str(ctx.entrada), str(carpeta / ctx.entrada.stem)])
    n = sum(1 for _ in carpeta.iterdir())
    if not n:
        carpeta.rmdir()
        return Resultado(sin_cambio=True, mensajes=["El PDF no tiene imágenes incrustadas."])
    return Resultado([carpeta], {"imagenes": n})


@operacion("ocr", "Convertir", "OCR (texto buscable)",
           "Reconoce el texto de un escaneo y le agrega una capa que se puede buscar y copiar.",
           sufijo="ocr", requiere=("ocrmypdf",),
           parametros=(Parametro("idioma", "Idioma", "opcion", "spa", opciones=(("spa", "Español"), ("eng", "Inglés"),
                                                                                   ("spa+eng", "Español e inglés"))),
                       Parametro("enderezar", "Enderezar páginas torcidas", "casilla", True),
                       Parametro("rotar", "Girar páginas de costado", "casilla", True),
                       Parametro("forzar", "Rehacer aunque ya tenga texto", "casilla", False),
                       Parametro("optimizar", "Optimización (0–3)", "entero", 1, minimo=0, maximo=3)),
           palabras=("escaneo", "escaneado", "reconocer", "buscable", "tesseract"))
def ocr(ctx):
    destino = ctx.salida()
    if ctx.simular:
        return Resultado(plan=[f"OCR ({ctx.p('idioma')}) → {destino.name}"])
    orden = ["ocrmypdf", "-l", ctx.p("idioma"), "--optimize", str(ctx.p("optimizar")), "--output-type", "pdf",
             "--force-ocr" if ctx.p("forzar") else "--skip-text"]
    if ctx.p("enderezar"):
        orden.append("--deskew")
    if ctx.p("rotar"):
        orden.append("--rotate-pages")
    try:
        correr(orden + [str(ctx.entrada), str(destino)], timeout=3600, mensaje="OCRmyPDF no pudo procesarlo")
    except ErrorOperacion:
        destino.unlink(missing_ok=True)
        raise
    if paginas_de(destino) != paginas_de(ctx.entrada):
        destino.unlink(missing_ok=True)
        raise ErrorOperacion("El resultado del OCR perdió páginas.")
    return Resultado([destino])


def texto_por_pagina(ruta) -> list[int]:
    import pymupdf
    with pymupdf.open(ruta) as doc:
        return [len(p.get_text().strip()) for p in doc]


@operacion("detectar_ocr", "Información", "¿Necesita OCR?",
           "Dice, página por página, si el PDF tiene texto o es solo imagen.", requiere=("py:pymupdf",),
           palabras=("escaneado", "imagen", "texto"))
def detectar_ocr(ctx):
    if ctx.simular:
        return Resultado(plan=[f"revisar {ctx.entrada.name}"])
    largos = texto_por_pagina(ctx.entrada)
    sin = [i + 1 for i, n in enumerate(largos) if n < 20]
    veredicto = "no" if not sin else ("sí" if len(sin) == len(largos) else "en parte")
    return Resultado(datos={"necesita_ocr": veredicto, "paginas_sin_texto": sin, "paginas": len(largos)},
                     mensajes=[f"Necesita OCR: {veredicto}" + (f" (páginas {', '.join(map(str, sin[:15]))}"
                                                              f"{'…' if len(sin) > 15 else ''})" if sin and veredicto != 'sí' else "")])


@operacion("miniatura", "Convertir", "Miniatura de una página", "Una imagen pequeña de una página (para vistas previas).",
           sufijo="miniatura", requiere=("py:pymupdf",),
           parametros=(Parametro("pagina", "Página", "entero", 1, minimo=1),
                       Parametro("ancho", "Ancho (px)", "entero", 240, minimo=32, maximo=2400),
                       Parametro("formato", "Formato", "opcion", "png", opciones=("png", "jpg", "webp"))))
def miniatura(ctx):
    import pymupdf
    destino = ctx.salida(extension=f".{ctx.p('formato')}", nombre=f"{ctx.entrada.stem}-p{ctx.p('pagina')}")
    if ctx.simular:
        return Resultado(plan=[f"miniatura → {destino.name}"])
    with pymupdf.open(ctx.entrada) as doc:
        if ctx.p("pagina") > doc.page_count:
            raise ErrorOperacion(f"El documento tiene {doc.page_count} páginas.")
        pagina = doc[ctx.p("pagina") - 1]
        zoom = ctx.p("ancho") / pagina.rect.width
        imagen = pagina.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
        if ctx.p("formato") == "webp":
            from PIL import Image
            Image.frombytes("RGB", (imagen.width, imagen.height), imagen.samples).save(destino, "WEBP", quality=80)
        else:
            imagen.save(destino, jpg_quality=82) if ctx.p("formato") == "jpg" else imagen.save(destino)
    return Resultado([destino])
