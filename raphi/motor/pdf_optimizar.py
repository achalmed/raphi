"""Optimizar: comprimir (por perfil o hasta un tamaño), comparar métodos, linearizar, reparar, validar y PDF/A."""
from __future__ import annotations

import shutil
from pathlib import Path

import pikepdf

from raphi.motor.base import ErrorOperacion, Parametro, Resultado, operacion, paginas_de
from raphi.motor.pdf_organizar import abrir
from raphi.motor.utiles import correr, tamano_legible

# Los perfiles de Ghostscript (los de pdf-suite): -dPDFSETTINGS y su resolución de imágenes.
PERFILES = {"screen": ("/screen", 72), "ebook": ("/ebook", 150), "printer": ("/printer", 300),
            "prepress": ("/prepress", 300)}
ETIQUETAS_PERFIL = (("ebook", "Recomendado (150 ppp, lectura en pantalla)"), ("screen", "Máxima (72 ppp, web y correo)"),
                    ("printer", "Para imprimir (300 ppp)"), ("prepress", "Imprenta (300 ppp, sin pérdida de color)"))


def ghostscript(entrada: Path, salida: Path, perfil: str = "ebook", ppp: int | None = None,
                extra: list[str] | None = None) -> Path:
    ajuste, resolucion = PERFILES[perfil]
    ppp = ppp or resolucion
    orden = ["gs", "-q", "-dNOPAUSE", "-dBATCH", "-dSAFER", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.7",
             f"-dPDFSETTINGS={ajuste}", "-dDetectDuplicateImages=true", "-dCompressFonts=true",
             "-dDownsampleColorImages=true", "-dDownsampleGrayImages=true", "-dDownsampleMonoImages=true",
             f"-dColorImageResolution={ppp}", f"-dGrayImageResolution={ppp}", f"-dMonoImageResolution={max(ppp, 300)}",
             *(extra or []), f"-sOutputFile={salida}", str(entrada)]
    correr(orden, timeout=900, mensaje=f"Ghostscript no pudo procesar {entrada.name}")
    return salida


def _intentos_hasta(tope_mb: float) -> list[tuple[str, int]]:
    """Del más fiel al más agresivo: el primero que entra en el tope es el que se queda."""
    return [("prepress", 300), ("printer", 200), ("ebook", 150), ("ebook", 120), ("screen", 96), ("screen", 72),
            ("screen", 50)]


@operacion("comprimir", "Optimizar", "Comprimir PDF",
           "Reduce el peso. Con un tope («10 MB»), prueba del más fiel al más agresivo y se queda con el primero que entra.",
           sufijo="comprimido", requiere=("gs",),
           parametros=(Parametro("perfil", "Nivel", "opcion", "ebook", opciones=ETIQUETAS_PERFIL),
                       Parametro("hasta", "Que pese menos de (MB, 0 = sin tope)", "tamano", 0, minimo=0,
                                 ayuda="p. ej. 10 para una mesa de partes virtual"),
                       Parametro("umbral", "Ganancia mínima (%)", "entero", 5, minimo=0, maximo=95,
                                 ayuda="si reduce menos, se conserva el original")),
           palabras=("reducir", "peso", "tamaño", "compress", "achicar"))
def comprimir(ctx):
    original = ctx.entrada.stat().st_size
    destino = ctx.salida()
    tope = ctx.p("hasta") or 0
    if ctx.simular:
        modo = f"hasta {tope:g} MB" if tope else f"perfil {ctx.p('perfil')}"
        return Resultado(plan=[f"comprimir {ctx.entrada.name} ({tamano_legible(original)}) con {modo} → {destino.name}"])
    paginas = paginas_de(ctx.entrada)
    intentos = _intentos_hasta(tope) if tope else [(ctx.p("perfil"), None)]
    mejor: tuple[int, Path, str] | None = None
    for i, (perfil, ppp) in enumerate(intentos):
        ctx.avisar(i / len(intentos), f"{perfil} {ppp or ''}".strip())
        prueba = ghostscript(ctx.entrada, ctx.temporal(".pdf"), perfil, ppp)
        peso = prueba.stat().st_size
        metodo = f"{perfil}{f' {ppp} ppp' if ppp else ''}"
        if tope and peso <= tope * 1024 * 1024:
            mejor = (peso, prueba, metodo)          # el primero que entra es el más fiel de los que entran
            break
        if mejor is None or peso < mejor[0]:
            mejor = (peso, prueba, metodo)          # si ninguno entra, el más liviano
    peso, prueba, metodo = mejor
    ganancia = 100 * (original - peso) / original if original else 0
    datos = {"original": original, "final": peso, "ganancia": round(ganancia, 1), "metodo": metodo}
    if paginas_de(prueba) != paginas:
        raise ErrorOperacion("La versión comprimida perdió páginas: se conserva el original.")
    if peso >= original or ganancia < (ctx.p("umbral") or 0):
        return Resultado(datos=datos, sin_cambio=True,
                         mensajes=[f"Sin ganancia suficiente ({ganancia:.1f} %): se conserva el original."])
    shutil.move(str(prueba), destino)
    mensajes = [f"{tamano_legible(original)} → {tamano_legible(peso)} (−{ganancia:.1f} %, {metodo})"]
    if tope and peso > tope * 1024 * 1024:
        mensajes.append(f"No bajó de {tope:g} MB: es lo más que se pudo sin perder páginas.")
        datos["tope_alcanzado"] = False
    return Resultado([destino], datos, mensajes)


@operacion("comparar_compresion", "Optimizar", "Comparar niveles de compresión",
           "Prueba los cuatro niveles y dice cuánto pesaría cada uno, sin guardar nada.", requiere=("gs",),
           palabras=("probar", "estimar"))
def comparar_compresion(ctx):
    original = ctx.entrada.stat().st_size
    if ctx.simular:
        return Resultado(plan=[f"probar {len(PERFILES)} niveles sobre {ctx.entrada.name}"])
    filas = []
    for i, perfil in enumerate(PERFILES):
        ctx.avisar(i / len(PERFILES), perfil)
        peso = ghostscript(ctx.entrada, ctx.temporal(".pdf"), perfil).stat().st_size
        filas.append({"perfil": perfil, "bytes": peso, "legible": tamano_legible(peso),
                      "ganancia": round(100 * (original - peso) / original, 1) if original else 0})
    return Resultado(datos={"original": original, "niveles": filas},
                     mensajes=[f"{f['perfil']}: {f['legible']} ({f['ganancia']:+.1f} %)" for f in filas])


@operacion("linearizar", "Optimizar", "Optimizar para la web",
           "Lineariza el PDF: la primera página se ve antes de que termine de descargarse.", sufijo="web",
           palabras=("linearizar", "fast web view", "web"))
def linearizar(ctx):
    destino = ctx.salida()
    if ctx.simular:
        return Resultado(plan=[f"linearizar → {destino.name}"])
    with abrir(ctx.entrada) as pdf:
        pdf.save(destino, linearize=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
    return Resultado([destino])


@operacion("reparar", "Optimizar", "Reparar PDF", "Reconstruye un PDF dañado (qpdf y, si no basta, Ghostscript).",
           sufijo="reparado", palabras=("arreglar", "dañado", "corrupto", "recuperar"))
def reparar(ctx):
    destino = ctx.salida()
    if ctx.simular:
        return Resultado(plan=[f"reparar {ctx.entrada.name} → {destino.name}"])
    try:
        with pikepdf.open(ctx.entrada, attempt_recovery=True) as pdf:
            if len(pdf.pages):
                pdf.save(destino)
                return Resultado([destino], {"metodo": "qpdf"}, ["Reconstruido con qpdf."])
    except pikepdf.PdfError:
        pass
    if not shutil.which("gs"):
        raise ErrorOperacion("qpdf no pudo repararlo y falta Ghostscript para el segundo intento.")
    ghostscript(ctx.entrada, destino, "prepress")
    return Resultado([destino], {"metodo": "ghostscript"}, ["Reescrito con Ghostscript."])


@operacion("validar", "Optimizar", "Validar estructura", "Revisa la estructura interna (qpdf --check) sin escribir nada.",
           palabras=("comprobar", "revisar", "check"))
def validar(ctx):
    if ctx.simular:
        return Resultado(plan=[f"revisar {ctx.entrada.name}"])
    try:
        with pikepdf.open(ctx.entrada) as pdf:
            problemas = pdf.check_pdf_syntax()
            paginas = len(pdf.pages)
    except pikepdf.PasswordError:
        return Resultado(datos={"valido": None}, mensajes=["Protegido con contraseña: no se puede revisar por dentro."])
    except pikepdf.PdfError as e:
        return Resultado(datos={"valido": False, "problemas": [str(e)]}, mensajes=[f"No abre: {e}"])
    return Resultado(datos={"valido": not problemas, "paginas": paginas, "problemas": problemas},
                     mensajes=["Estructura correcta."] if not problemas else [f"{len(problemas)} problema(s)"] + problemas[:10])


def es_pdfa(ruta: Path) -> str | None:
    """«2B» si declara PDF/A-2b en su XMP (no es una validación completa: eso es veraPDF)."""
    try:
        with pikepdf.open(ruta) as pdf:
            meta = pdf.open_metadata()
            parte, conf = meta.get("pdfaid:part"), meta.get("pdfaid:conformance")
            return f"{parte}{conf or ''}".upper() if parte else None
    except Exception:
        return None


@operacion("pdfa", "Optimizar", "Convertir a PDF/A (archivo)",
           "PDF/A-2b, el formato de conservación a largo plazo de los archivos públicos.", sufijo="pdfa",
           requiere=("gs",), palabras=("archivar", "conservación", "pdf/a", "archivo"))
def pdfa(ctx):
    destino = ctx.salida()
    if ctx.simular:
        return Resultado(plan=[f"PDF/A-2b → {destino.name}"])
    correr(["gs", "-q", "-dPDFA=2", "-dBATCH", "-dNOPAUSE", "-dSAFER", "-sColorConversionStrategy=UseDeviceIndependentColor",
            "-sDEVICE=pdfwrite", "-dPDFACompatibilityPolicy=1", f"-sOutputFile={destino}", str(ctx.entrada)],
           timeout=900, mensaje="Ghostscript no pudo producir el PDF/A")
    nivel = es_pdfa(destino)
    if nivel != "2B":
        destino.unlink(missing_ok=True)
        raise ErrorOperacion(f"La salida no declara PDF/A-2b (declara: {nivel or 'nada'}).")
    if paginas_de(destino) != paginas_de(ctx.entrada):
        destino.unlink(missing_ok=True)
        raise ErrorOperacion("El PDF/A perdió páginas.")
    return Resultado([destino], {"pdfa": nivel})
