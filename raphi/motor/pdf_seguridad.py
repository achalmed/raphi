"""Seguridad: cifrar (AES-256), descifrar y leer las firmas incrustadas (la verificación, en pdf_avanzado.py)."""
from __future__ import annotations

import pikepdf

from raphi.motor.base import ErrorOperacion, Parametro, Resultado, operacion


@operacion("cifrar", "Seguridad", "Proteger con contraseña", "Cifra el PDF con AES-256 y, si se quiere, limita imprimir o copiar.",
           sufijo="protegido",
           parametros=(Parametro("clave", "Contraseña para abrirlo", "clave", "", obligatorio=True),
                       Parametro("propietario", "Contraseña de permisos", "clave", "", ayuda="vacío = la misma"),
                       Parametro("imprimir", "Permitir imprimir", "casilla", True),
                       Parametro("copiar", "Permitir copiar texto", "casilla", True),
                       Parametro("modificar", "Permitir modificar", "casilla", False)),
           palabras=("contraseña", "proteger", "bloquear", "encrypt", "password"))
def cifrar(ctx):
    destino = ctx.salida()
    if ctx.simular:
        return Resultado(plan=[f"cifrar con AES-256 → {destino.name}"])
    from raphi.motor.pdf_organizar import abrir
    permisos = pikepdf.Permissions(print_lowres=ctx.p("imprimir"), print_highres=ctx.p("imprimir"),
                                   extract=ctx.p("copiar"), modify_other=ctx.p("modificar"),
                                   modify_annotation=ctx.p("modificar"), modify_form=ctx.p("modificar"),
                                   modify_assembly=ctx.p("modificar"))
    with abrir(ctx.entrada) as pdf:
        pdf.save(destino, encryption=pikepdf.Encryption(user=ctx.p("clave"), owner=ctx.p("propietario") or ctx.p("clave"),
                                                         R=6, allow=permisos))
    with pikepdf.open(destino, password=ctx.p("clave")) as prueba:
        if not prueba.is_encrypted:
            raise ErrorOperacion("La salida no quedó cifrada.")
    return Resultado([destino])


@operacion("descifrar", "Seguridad", "Quitar contraseña", "Abre un PDF protegido con su contraseña y lo guarda sin ella.",
           sufijo="sin-clave",
           parametros=(Parametro("clave", "Contraseña", "clave", "", obligatorio=True),),
           palabras=("desbloquear", "decrypt", "unlock"))
def descifrar(ctx):
    destino = ctx.salida()
    if ctx.simular:
        return Resultado(plan=[f"descifrar → {destino.name}"])
    try:
        pdf = pikepdf.open(ctx.entrada, password=ctx.p("clave"))
    except pikepdf.PasswordError as e:
        raise ErrorOperacion("La contraseña no es la correcta.") from e
    with pdf:
        pdf.save(destino)
    return Resultado([destino])


def firmas(pdf: pikepdf.Pdf) -> list[dict]:
    """Las firmas incrustadas (campos /Sig con /ByteRange, PAdES): quién y cuándo, sin verificar la cadena."""
    salida = []
    campos = pdf.Root.get("/AcroForm", {}).get("/Fields", []) if "/AcroForm" in pdf.Root else []
    pendientes = list(campos)
    while pendientes:
        c = pendientes.pop()
        if "/Kids" in c:
            pendientes.extend(c.Kids)
        v = c.get("/V")
        if c.get("/FT") == "/Sig" and v is not None and "/ByteRange" in v:
            salida.append({"campo": str(c.get("/T", "")), "nombre": str(v.get("/Name", "")),
                           "fecha": str(v.get("/M", "")), "motivo": str(v.get("/Reason", "")),
                           "lugar": str(v.get("/Location", "")), "subfiltro": str(v.get("/SubFilter", ""))})
    return salida
