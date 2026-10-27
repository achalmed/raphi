"""Organizar: unir, dividir, extraer, rotar, reordenar, eliminar y componer (la mesa de trabajo)."""
from __future__ import annotations

from pathlib import Path

import pikepdf

from raphi.motor.base import ErrorOperacion, Parametro, Resultado, operacion
from raphi.motor.utiles import interpretar_paginas


def abrir(ruta: Path, clave: str = "") -> pikepdf.Pdf:
    try:
        return pikepdf.open(ruta, password=clave or "")
    except pikepdf.PasswordError as e:
        raise ErrorOperacion(f"{ruta.name} está protegido con contraseña: descífrelo antes.") from e
    except pikepdf.PdfError as e:
        raise ErrorOperacion(f"{ruta.name} no se puede leer como PDF (pruebe «Reparar»).") from e


def guardar(pdf: pikepdf.Pdf, ruta: Path, **kw) -> Path:
    pdf.save(ruta, **kw)
    return ruta


@operacion("unir", "Organizar", "Unir PDF", "Junta varios PDF en uno, en el orden dado.",
           entrada="pdfs", lote=False, minimo_entradas=2, sufijo="unido",
           parametros=(Parametro("nombre", "Nombre del archivo", "texto", "unido", ayuda="sin «.pdf»"),
                       Parametro("marcadores", "Un marcador por archivo", "casilla", True)),
           palabras=("juntar", "combinar", "merge", "concatenar"))
def unir(ctx):
    total = sum(len(abrir(e).pages) for e in ctx.entradas)
    destino = ctx.salida(nombre=ctx.p("nombre") or "unido")
    if ctx.simular:
        return Resultado(plan=[f"unir {len(ctx.entradas)} PDF ({total} páginas) en {destino.name}"])
    salida = pikepdf.new()
    with salida.open_outline() as indice:
        for i, e in enumerate(ctx.entradas):
            ctx.avisar(i / len(ctx.entradas), e.name)
            with abrir(e) as fuente:
                inicio = len(salida.pages)
                salida.pages.extend(fuente.pages)
                if ctx.p("marcadores"):
                    indice.root.append(pikepdf.OutlineItem(e.stem, inicio))
    guardar(salida, destino)
    if len(salida.pages) != total:
        raise ErrorOperacion("El PDF unido no tiene todas las páginas.")
    return Resultado([destino], {"paginas": total})


@operacion("dividir", "Organizar", "Dividir PDF", "Parte un PDF por rangos o cada N páginas.",
           sufijo="parte",
           parametros=(Parametro("cada", "Páginas por parte (0 = una por página)", "entero", 0, minimo=0),
                       Parametro("rangos", "O por rangos (separados por «;»)", "texto", "",
                                 ayuda="«1-3; 4-10; 11-z»: un PDF por rango")),
           palabras=("separar", "partir", "split", "cortar"))
def dividir(ctx):
    with abrir(ctx.entrada) as pdf:
        total = len(pdf.pages)
        if ctx.p("rangos"):
            grupos = [interpretar_paginas(r, total) for r in ctx.p("rangos").split(";") if r.strip()]
        else:
            cada = ctx.p("cada") or 1
            grupos = [list(range(i, min(i + cada, total))) for i in range(0, total, cada)]
        ancho = len(str(len(grupos)))
        nombres = [ctx.salida(nombre=f"{ctx.entrada.stem}_parte{str(i + 1).zfill(ancho)}") for i in range(len(grupos))]
        if ctx.simular:
            return Resultado(plan=[f"{n.name}: páginas {g[0] + 1}–{g[-1] + 1} ({len(g)})" for n, g in zip(nombres, grupos)])
        salidas = []
        for i, (grupo, destino) in enumerate(zip(grupos, nombres)):
            ctx.avisar(i / len(grupos), destino.name)
            parte = pikepdf.new()
            for n in grupo:
                parte.pages.append(pdf.pages[n])
            salidas.append(guardar(parte, destino))
    return Resultado(salidas, {"partes": len(salidas), "paginas": total})


@operacion("extraer", "Organizar", "Extraer páginas", "Saca las páginas elegidas a un PDF nuevo.",
           sufijo="extracto",
           parametros=(Parametro("paginas", "Páginas", "paginas", "1", obligatorio=True,
                                 ayuda="1-5 · 1,3,10-12 · 10-z · -3 (las tres últimas)"),),
           palabras=("sacar", "seleccionar"))
def extraer(ctx):
    with abrir(ctx.entrada) as pdf:
        indices = interpretar_paginas(ctx.p("paginas"), len(pdf.pages))
        destino = ctx.salida()
        if ctx.simular:
            return Resultado(plan=[f"{destino.name}: {len(indices)} páginas"])
        nuevo = pikepdf.new()
        for n in indices:
            nuevo.pages.append(pdf.pages[n])
        guardar(nuevo, destino)
    return Resultado([destino], {"paginas": len(indices)})


@operacion("rotar", "Organizar", "Rotar páginas", "Gira las páginas elegidas (o todas).",
           sufijo="rotado",
           parametros=(Parametro("angulo", "Ángulo", "opcion", "90",
                                 opciones=(("90", "90° a la derecha"), ("180", "180°"), ("270", "90° a la izquierda"))),
                       Parametro("paginas", "Páginas (vacío = todas)", "paginas", "")),
           palabras=("girar", "voltear", "orientación"))
def rotar(ctx):
    with abrir(ctx.entrada) as pdf:
        indices = interpretar_paginas(ctx.p("paginas"), len(pdf.pages))
        destino = ctx.salida()
        if ctx.simular:
            return Resultado(plan=[f"rotar {len(indices)} páginas {ctx.p('angulo')}° → {destino.name}"])
        for n in indices:
            pdf.pages[n].rotate(int(ctx.p("angulo")), relative=True)
        guardar(pdf, destino)
    return Resultado([destino], {"rotadas": len(indices)})


@operacion("reordenar", "Organizar", "Reordenar páginas", "Pone las páginas en el orden escrito (vacío = invertir).",
           sufijo="reordenado",
           parametros=(Parametro("orden", "Nuevo orden", "paginas", "", ayuda="3,1,2,4-z · vacío invierte el documento"),),
           palabras=("ordenar", "invertir", "mover"))
def reordenar(ctx):
    with abrir(ctx.entrada) as pdf:
        total = len(pdf.pages)
        indices = interpretar_paginas(ctx.p("orden"), total) if ctx.p("orden") else list(range(total - 1, -1, -1))
        faltan = sorted(set(range(total)) - set(indices))
        indices += faltan                       # lo que no se nombró va al final, en su orden: no se pierde nada
        destino = ctx.salida()
        if ctx.simular:
            return Resultado(plan=[f"orden {', '.join(str(i + 1) for i in indices[:20])}{'…' if total > 20 else ''}"
                                   f" → {destino.name}"])
        nuevo = pikepdf.new()
        for n in indices:
            nuevo.pages.append(pdf.pages[n])
        guardar(nuevo, destino)
    return Resultado([destino], {"paginas": total, "al_final": [f + 1 for f in faltan]})


@operacion("eliminar", "Organizar", "Eliminar páginas", "Quita las páginas elegidas.",
           sufijo="sin-paginas",
           parametros=(Parametro("paginas", "Páginas a quitar", "paginas", "", obligatorio=True),),
           palabras=("borrar", "quitar", "suprimir"))
def eliminar(ctx):
    with abrir(ctx.entrada) as pdf:
        total = len(pdf.pages)
        quitar = set(interpretar_paginas(ctx.p("paginas"), total, vacio_es_todas=False))
        if len(quitar) >= total:
            raise ErrorOperacion("No se pueden quitar todas las páginas.")
        destino = ctx.salida()
        if ctx.simular:
            return Resultado(plan=[f"quitar {len(quitar)} de {total} páginas → {destino.name}"])
        for n in sorted(quitar, reverse=True):
            del pdf.pages[n]
        guardar(pdf, destino)
    return Resultado([destino], {"quedan": total - len(quitar)})


@operacion("componer", "Organizar", "Componer (mesa de trabajo)",
           "Arma un PDF con páginas de varios archivos, en cualquier orden, rotadas o en blanco.",
           entrada="pdfs", lote=False, sufijo="compuesto",
           parametros=(Parametro("plan", "Plan de páginas", "json", None, obligatorio=True,
                                 ayuda='[{"archivo": 0, "pagina": 3, "rotar": 90}, {"blanca": true}, …]'),
                       Parametro("nombre", "Nombre del archivo", "texto", "compuesto")),
           palabras=("organizar", "mesa", "insertar", "página en blanco"))
def componer(ctx):
    plan = ctx.p("plan")
    if not isinstance(plan, list) or not plan:
        raise ErrorOperacion("El plan de páginas está vacío.")
    fuentes = [abrir(e) for e in ctx.entradas]
    try:
        for i, paso in enumerate(plan):
            if paso.get("blanca"):
                continue
            a, n = int(paso.get("archivo", 0)), int(paso.get("pagina", 1))
            if not 0 <= a < len(fuentes) or not 1 <= n <= len(fuentes[a].pages):
                raise ErrorOperacion(f"Paso {i + 1} del plan: no existe la página {n} del archivo {a + 1}.")
        destino = ctx.salida(nombre=ctx.p("nombre") or "compuesto", extension=".pdf")
        if ctx.simular:
            return Resultado(plan=[f"{len(plan)} páginas → {destino.name}"])
        nuevo = pikepdf.new()
        for paso in plan:
            if paso.get("blanca"):
                ref = nuevo.pages[-1] if len(nuevo.pages) else (fuentes[0].pages[0] if fuentes else None)
                caja = list(ref.mediabox) if ref is not None else [0, 0, 595, 842]
                nuevo.add_blank_page(page_size=(float(caja[2]) - float(caja[0]), float(caja[3]) - float(caja[1])))
                continue
            nuevo.pages.append(fuentes[int(paso.get("archivo", 0))].pages[int(paso.get("pagina", 1)) - 1])
            if paso.get("rotar"):
                nuevo.pages[-1].rotate(int(paso["rotar"]), relative=True)
        guardar(nuevo, destino)
    finally:
        for f in fuentes:
            f.close()
    return Resultado([destino], {"paginas": len(plan)})
