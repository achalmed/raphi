"""Editar y sellar: marca de agua, numerar, foliar (expedientes), sello de recepción y metadatos.

Con PyMuPDF, que escribe texto sobre la página respetando su rotación. La foliación sigue la práctica de la
administración pública peruana: número correlativo en el ángulo superior derecho, con la opción de foliar de atrás
hacia adelante (el último documento recibe el folio 1) y de continuar una cuenta anterior.
"""
from __future__ import annotations

import datetime as dt
import math

from raphi.motor.base import ErrorOperacion, Parametro, Resultado, operacion
from raphi.motor.utiles import POSICIONES, color_rgb, interpretar_paginas, punto_en


def _doc(ruta):
    import pymupdf
    try:
        doc = pymupdf.open(ruta)
    except Exception as e:
        raise ErrorOperacion(f"{ruta.name} no se puede leer como PDF.") from e
    if doc.needs_pass:
        doc.close()
        raise ErrorOperacion(f"{ruta.name} está protegido con contraseña: descífrelo antes.")
    return doc


def _guardar(doc, destino):
    doc.save(destino, garbage=3, deflate=True)
    doc.close()
    return destino


def _texto(pagina, texto: str, posicion: str, tamano: float, color, recuadro: bool = False, fuente: str = "helv",
           opacidad: float = 1.0, margen: float = 28):
    """Escribe una o varias líneas en una posición, sobre la página tal como se ve (respeta /Rotate)."""
    import pymupdf
    lineas = texto.splitlines() or [""]
    ancho = max(pymupdf.get_text_length(l, fontname=fuente, fontsize=tamano) for l in lineas) + (8 if recuadro else 0)
    alto = tamano * 1.25 * len(lineas) + (6 if recuadro else 0)
    visible = pagina.rect                             # la página como se ve
    x, y = punto_en(visible, posicion, ancho, alto, margen)
    caja = pymupdf.Rect(x, y, x + ancho, y + alto) * pagina.derotation_matrix
    if recuadro:
        pagina.draw_rect(caja, color=color, width=0.8, fill=(1, 1, 1), fill_opacity=0.9 * opacidad,
                         stroke_opacity=opacidad)
    for i, linea in enumerate(lineas):
        punto = pymupdf.Point(x + (4 if recuadro else 0), y + (3 if recuadro else 0) + tamano * (1.0 + 1.25 * i))
        pagina.insert_text(punto * pagina.derotation_matrix, linea, fontname=fuente, fontsize=tamano, color=color,
                           rotate=pagina.rotation, fill_opacity=opacidad, stroke_opacity=opacidad)


@operacion("marca_agua", "Editar", "Marca de agua", "Escribe un texto en diagonal (o recto) sobre las páginas.",
           sufijo="marca", requiere=("py:pymupdf",),
           parametros=(Parametro("texto", "Texto", "texto", "BORRADOR", obligatorio=True),
                       Parametro("tamano", "Tamaño (pt)", "entero", 60, minimo=6, maximo=300),
                       Parametro("opacidad", "Opacidad (0–1)", "decimal", 0.18, minimo=0.02, maximo=1),
                       Parametro("angulo", "Ángulo", "entero", 45, minimo=-90, maximo=90),
                       Parametro("color", "Color", "color", "#C0392B"),
                       Parametro("paginas", "Páginas (vacío = todas)", "paginas", "")),
           palabras=("watermark", "borrador", "confidencial", "copia"))
def marca_agua(ctx):
    import pymupdf
    doc = _doc(ctx.entrada)
    indices = interpretar_paginas(ctx.p("paginas"), doc.page_count)
    destino = ctx.salida()
    if ctx.simular:
        doc.close()
        return Resultado(plan=[f"«{ctx.p('texto')}» en {len(indices)} páginas → {destino.name}"])
    color, tam, ang = color_rgb(ctx.p("color")), ctx.p("tamano"), ctx.p("angulo")
    for n in indices:
        pagina = doc[n]
        r = pagina.rect
        largo = pymupdf.get_text_length(ctx.p("texto"), fontname="helv", fontsize=tam)
        centro = pymupdf.Point(r.width / 2, r.height / 2)
        rad = math.radians(ang)
        inicio = pymupdf.Point(centro.x - largo / 2 * math.cos(rad), centro.y + largo / 2 * math.sin(rad) + tam / 3)
        matriz = pymupdf.Matrix(1, 1).prerotate(ang)
        pagina.insert_text(inicio * pagina.derotation_matrix, ctx.p("texto"), fontname="helv", fontsize=tam,
                           color=color, fill_opacity=ctx.p("opacidad"), stroke_opacity=ctx.p("opacidad"),
                           morph=(inicio * pagina.derotation_matrix, matriz), rotate=pagina.rotation)
    return Resultado([_guardar(doc, destino)], {"paginas": len(indices)})


@operacion("numerar", "Editar", "Numerar páginas", "Pone el número de página («Página 3 de 10» o como se quiera).",
           sufijo="numerado", requiere=("py:pymupdf",),
           parametros=(Parametro("formato", "Formato", "texto", "{n}", ayuda="{n} número · {total} total · «Página {n} de {total}»"),
                       Parametro("posicion", "Posición", "opcion", "abajo-centro", opciones=POSICIONES),
                       Parametro("inicio", "Primer número", "entero", 1, minimo=0),
                       Parametro("desde", "Desde la página", "entero", 1, minimo=1, ayuda="p. ej. 2 para no numerar la carátula"),
                       Parametro("tamano", "Tamaño (pt)", "entero", 10, minimo=5, maximo=48),
                       Parametro("color", "Color", "color", "#000000")),
           palabras=("paginación", "números", "page numbers"))
def numerar(ctx):
    doc = _doc(ctx.entrada)
    desde = ctx.p("desde") - 1
    if desde >= doc.page_count:
        doc.close()
        raise ErrorOperacion(f"El documento tiene {doc.page_count} páginas.")
    destino = ctx.salida()
    total = doc.page_count - desde + ctx.p("inicio") - 1
    if ctx.simular:
        doc.close()
        return Resultado(plan=[f"numerar {doc.page_count - desde} páginas desde la {desde + 1} → {destino.name}"])
    try:
        for i, n in enumerate(range(desde, doc.page_count)):
            texto = ctx.p("formato").format(n=ctx.p("inicio") + i, total=total)
            _texto(doc[n], texto, ctx.p("posicion"), ctx.p("tamano"), color_rgb(ctx.p("color")))
    except (KeyError, IndexError, ValueError) as e:
        doc.close()
        raise ErrorOperacion("El formato admite solo {n} y {total}.") from e
    return Resultado([_guardar(doc, destino)], {"ultimo": total})


@operacion("foliar", "Editar", "Foliar expediente",
           "Numera los folios en el ángulo superior derecho, correlativos o de atrás hacia adelante, siguiendo una cuenta anterior si la hay.",
           sufijo="foliado", requiere=("py:pymupdf",),
           parametros=(Parametro("inicio", "Primer folio", "entero", 1, minimo=1, ayuda="para continuar un expediente ya foliado"),
                       Parametro("orden", "Orden", "opcion", "ascendente",
                                 opciones=(("ascendente", "De la primera a la última"),
                                           ("inverso", "De atrás hacia adelante (el último es el folio 1)"))),
                       Parametro("formato", "Formato", "texto", "{n}", ayuda="{n} · «Folio {n}» · «{n:04d}»"),
                       Parametro("posicion", "Posición", "opcion", "arriba-derecha", opciones=POSICIONES),
                       Parametro("recuadro", "Con recuadro", "casilla", True),
                       Parametro("tamano", "Tamaño (pt)", "entero", 11, minimo=6, maximo=36),
                       Parametro("color", "Color", "color", "#1F3A93")),
           palabras=("folios", "expediente", "foliación", "foliado"))
def foliar(ctx):
    doc = _doc(ctx.entrada)
    destino = ctx.salida()
    total = doc.page_count
    inicio = ctx.p("inicio")
    if ctx.simular:
        doc.close()
        return Resultado(plan=[f"folios {inicio}–{inicio + total - 1} ({ctx.p('orden')}) → {destino.name}"])
    try:
        for i in range(total):
            folio = inicio + (i if ctx.p("orden") == "ascendente" else total - 1 - i)
            _texto(doc[i], ctx.p("formato").format(n=folio), ctx.p("posicion"), ctx.p("tamano"),
                   color_rgb(ctx.p("color")), recuadro=ctx.p("recuadro"), fuente="hebo", margen=20)
    except (KeyError, IndexError, ValueError) as e:
        doc.close()
        raise ErrorOperacion("El formato admite {n} (y {n:04d} para rellenar con ceros).") from e
    return Resultado([_guardar(doc, destino)], {"primero": inicio, "ultimo": inicio + total - 1, "folios": total})


@operacion("sello", "Editar", "Sello de recepción",
           "Estampa el sello «RECIBIDO» con la fecha y la hora, los folios y lo que se escriba.",
           sufijo="sellado", requiere=("py:pymupdf",),
           parametros=(Parametro("titulo", "Título", "texto", "RECIBIDO"),
                       Parametro("entidad", "Oficina o entidad", "texto", ""),
                       Parametro("fecha", "Fecha y hora", "texto", "", ayuda="vacío = ahora"),
                       Parametro("folios", "Contar los folios", "casilla", True),
                       Parametro("nota", "Más líneas", "multilinea", "", ayuda="registro, firma…"),
                       Parametro("posicion", "Posición", "opcion", "arriba-derecha", opciones=POSICIONES),
                       Parametro("pagina", "Página", "entero", 1, minimo=1),
                       Parametro("color", "Color", "color", "#1F3A93")),
           palabras=("cargo", "recepción", "recibido", "mesa de partes", "estampar"))
def sello(ctx):
    doc = _doc(ctx.entrada)
    n = ctx.p("pagina") - 1
    if n >= doc.page_count:
        doc.close()
        raise ErrorOperacion(f"El documento tiene {doc.page_count} páginas.")
    momento = ctx.p("fecha") or dt.datetime.now().strftime("%d/%m/%Y %H:%M")
    lineas = [ctx.p("titulo")] + ([ctx.p("entidad")] if ctx.p("entidad") else []) + [momento]
    if ctx.p("folios"):
        lineas.append(f"Folios: {doc.page_count}")
    lineas += [l for l in (ctx.p("nota") or "").splitlines() if l.strip()]
    destino = ctx.salida()
    if ctx.simular:
        doc.close()
        return Resultado(plan=[f"sello en la página {n + 1}: {' · '.join(lineas)} → {destino.name}"])
    _texto(doc[n], "\n".join(lineas), ctx.p("posicion"), 9, color_rgb(ctx.p("color")), recuadro=True, fuente="hebo")
    return Resultado([_guardar(doc, destino)], {"sello": lineas})


@operacion("metadatos", "Editar", "Editar metadatos",
           "Título, autor, asunto y palabras clave (DocInfo y XMP); o el título tomado del nombre del archivo.",
           sufijo="metadatos",
           parametros=(Parametro("titulo", "Título", "texto", ""), Parametro("autor", "Autor", "texto", ""),
                       Parametro("asunto", "Asunto", "texto", ""), Parametro("palabras", "Palabras clave", "texto", ""),
                       Parametro("titulo_del_nombre", "Título desde el nombre del archivo", "casilla", False)),
           palabras=("propiedades", "título", "autor", "xmp"))
def metadatos(ctx):
    from raphi.motor.pdf_organizar import abrir
    valores = {"dc:title": ctx.p("titulo") or (ctx.entrada.stem.replace("_", " ").replace("-", " ").strip()
                                               if ctx.p("titulo_del_nombre") else ""),
               "dc:creator": ctx.p("autor"), "dc:description": ctx.p("asunto"), "pdf:Keywords": ctx.p("palabras")}
    valores = {k: v for k, v in valores.items() if v}
    if not valores:
        raise ErrorOperacion("No hay nada que escribir: complete al menos un campo.")
    destino = ctx.salida()
    if ctx.simular:
        return Resultado(plan=[f"{k} = {v}" for k, v in valores.items()] + [f"→ {destino.name}"])
    with abrir(ctx.entrada) as pdf:
        with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
            for k, v in valores.items():
                meta[k] = [v] if k == "dc:creator" else v
        pdf.save(destino)
    return Resultado([destino], {"escritos": valores})


@operacion("quitar_metadatos", "Seguridad", "Quitar metadatos",
           "Borra autor, programa, fechas y el XMP del PDF antes de compartirlo.", sufijo="limpio",
           palabras=("privacidad", "anonimizar", "limpiar", "metadata"))
def quitar_metadatos(ctx):
    from raphi.motor.pdf_organizar import abrir
    destino = ctx.salida()
    if ctx.simular:
        return Resultado(plan=[f"quitar DocInfo y XMP → {destino.name}"])
    with abrir(ctx.entrada) as pdf:
        for clave in list(pdf.docinfo.keys()):
            del pdf.docinfo[clave]
        if "/Metadata" in pdf.Root:
            del pdf.Root.Metadata
        pdf.save(destino)
    return Resultado([destino])
