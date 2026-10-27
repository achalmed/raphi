"""Lo que Raphi ofrece a los demás módulos: «pdf.v1» y «conversion.v1».

Los demás la APROVECHAN, nunca la necesitan: `pdf = tiqsi.modulo.opcional("pdf.v1")`; si es None, siguen como antes.
Todas las funciones son asíncronas (el motor corre en un hilo) y trabajan con rutas del módulo que llama: Raphi lee
la entrada y escribe la salida en la carpeta que se le indique; nunca escribe en la base ni en la carpeta de nadie
por su cuenta.

    pdf = opcional("pdf.v1")
    if pdf:
        informe = await pdf.ejecutar("ocr", [ruta], {"idioma": "spa"}, destino=carpeta)
        png = await pdf.miniatura(ruta, pagina=1, ancho=320)
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from tiqsi import Superficie


async def operaciones() -> list[dict]:
    from raphi import motor
    return motor.operaciones(solo_disponibles=True)


async def ejecutar(operacion: str, rutas: list[str | Path], params: dict | None = None, *,
                   destino: str | Path | None = None, simular: bool = False) -> dict:
    """Corre una operación (o «receta:<id>») y devuelve su informe (`Informe.a_dict()`)."""
    from raphi import motor, recetas
    if operacion.startswith("receta:"):
        r = recetas.buscar(operacion.split(":", 1)[1])
        informe = await asyncio.to_thread(recetas.aplicar, r, rutas, destino=destino, simular=simular)
    else:
        informe = await asyncio.to_thread(motor.ejecutar, operacion, rutas, params or {}, destino=destino,
                                          simular=simular)
    return informe.a_dict()


async def miniatura(ruta: str | Path, pagina: int = 1, ancho: int = 240) -> bytes:
    def hacer() -> bytes:
        import pymupdf
        with pymupdf.open(ruta) as doc:
            p = doc[pagina - 1]
            zoom = ancho / p.rect.width
            return p.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False).tobytes("png")
    return await asyncio.to_thread(hacer)


async def texto(ruta: str | Path) -> str:
    def hacer() -> str:
        import pymupdf
        with pymupdf.open(ruta) as doc:
            return "\n\f".join(p.get_text() for p in doc)
    return await asyncio.to_thread(hacer)


async def info(ruta: str | Path) -> dict:
    from raphi.motor.pdf_info import informacion
    return await asyncio.to_thread(informacion, Path(ruta))


async def verificar_firmas(ruta: str | Path) -> list[dict]:
    """Cada firma: firmante, fecha, integridad y, con raíces de confianza (RAPHI_RAICES), su cadena."""
    from raphi.motor.pdf_avanzado import verificar
    return await asyncio.to_thread(verificar, Path(ruta))


async def formatos_de(nombre: str) -> list[dict]:
    from raphi.motor.medios import formatos_de as f
    return f(nombre)


async def convertir(ruta: str | Path, formato: str, destino: str | Path | None = None) -> dict:
    """Convierte un archivo al formato pedido con la operación que corresponda (la del menú de formatos)."""
    from raphi.motor.medios import formatos_de as f
    opcion = next((x for x in f(ruta) if x["a"] == formato), None)
    if opcion is None:
        from raphi.motor import ErrorOperacion
        raise ErrorOperacion(f"{Path(ruta).name} no se convierte a {formato}.")
    return await ejecutar(opcion["operacion"], [ruta], opcion["params"], destino=destino)


PDF_V1 = Superficie("pdf.v1", {
    "operaciones": lambda: operaciones, "ejecutar": lambda: ejecutar, "miniatura": lambda: miniatura,
    "texto": lambda: texto, "info": lambda: info, "verificar_firmas": lambda: verificar_firmas,
}, "raphi/contrato.py")

CONVERSION_V1 = Superficie("conversion.v1", {
    "formatos_de": lambda: formatos_de, "convertir": lambda: convertir,
}, "raphi/contrato.py")
