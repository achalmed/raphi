"""Fechas y nombres de fotos y videos de cámara: auditar y ordenar una carpeta.

Envuelve `backends/photo-metadata` (llegó de scripts-linux el 2026-10-31), que sigue siendo una CLI completa con OCR de
la marca impresa, plan de renombrado editable, deshacer y digiKam. Ese backend trabaja sobre la carpeta misma; aquí
se respeta el principio 2 de `base.py`: «ordenar» trabaja sobre una copia en una carpeta nueva y «auditar» solo lee.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from raphi.motor.base import ErrorOperacion, Parametro, Resultado, operacion
from raphi.motor.medios import IMG, VID
from raphi.motor.utiles import correr

FOTOS = Path(__file__).resolve().parents[2] / "backends" / "photo-metadata" / "main.py"
HORAS = 3600


def _carpeta(ctx) -> Path:
    if not ctx.entrada.is_dir():
        raise ErrorOperacion(f"{ctx.entrada.name}: se espera una carpeta de fotos o videos.")
    return ctx.entrada


def _medios_de(carpeta: Path) -> list[Path]:
    """Las fotos y videos de la carpeta, sin subcarpetas (como el backend)."""
    return sorted(p for p in carpeta.iterdir() if p.is_file() and p.suffix.lower() in IMG + VID)


@operacion("auditar_fechas_fotos", "Información", "Auditar fechas de fotos",
           "Compara la fecha del nombre de cada foto o video con la de sus metadatos; solo lee.",
           entrada="archivos", extensiones=(), requiere=("exiftool",),
           parametros=(Parametro("anio", "Año esperado (0: el del nombre de la carpeta)", "entero", 0, minimo=0),),
           palabras=("exif", "fecha", "cámara", "fotos", "auditoría"))
def auditar_fechas_fotos(ctx):
    carpeta = _carpeta(ctx)
    orden = [sys.executable, str(FOTOS), "audit-dates", str(carpeta)]
    if ctx.p("anio"):
        orden += ["--year", str(ctx.p("anio"))]
    if ctx.simular:
        return Resultado(plan=[f"{carpeta.name}: {len(_medios_de(carpeta))} archivo(s) que leer, nada que escribir"])
    r = correr(orden, timeout=2 * HORAS, entorno={"NO_COLOR": "1"}, mensaje="La auditoría falló")
    lineas = [l for l in (r.stdout or "").splitlines() if l.strip()]
    return Resultado(mensajes=lineas[-40:], datos={"salida": r.stdout})


@operacion("ordenar_fotos_por_fecha", "Medios", "Ordenar fotos por fecha",
           "Copia la carpeta y en la copia corrige extensiones, lleva los nombres a AAAAMMDD_HHMMSS y escribe la fecha "
           "en los metadatos. El original no se toca.",
           entrada="archivos", extensiones=(), sufijo="ordenadas", requiere=("exiftool",),
           parametros=(Parametro("incrustar", "Escribir la fecha en EXIF/QuickTime", "casilla", True),
                       Parametro("nombre_manda", "Fotos escaneadas: el nombre manda sobre el EXIF", "casilla", False)),
           palabras=("renombrar", "whatsapp", "cámara", "exif", "fecha", "fotos", "ordenar"))
def ordenar_fotos_por_fecha(ctx):
    carpeta = _carpeta(ctx)
    medios = _medios_de(carpeta)
    if not medios:
        raise ErrorOperacion(f"{carpeta.name}: no hay fotos ni videos (sin contar subcarpetas).")
    if ctx.simular:
        return Resultado(plan=[f"{carpeta.name}: {len(medios)} archivo(s) → copia «{carpeta.name}_ordenadas»"])
    copia = ctx.carpeta_salida(nombre=f"{carpeta.name}_{ctx.sufijo or 'ordenadas'}")
    for i, medio in enumerate(medios):
        shutil.copy2(medio, copia / medio.name)
        ctx.avisar(0.4 * (i + 1) / len(medios), f"Copiando {medio.name}")
    ctx.avisar(0.45, "Corrigiendo nombres y extensiones")
    correr([sys.executable, str(FOTOS), "fix-names", str(copia), "--execute"], timeout=2 * HORAS,
           entorno={"NO_COLOR": "1"}, mensaje="No se pudieron corregir los nombres")
    if ctx.p("incrustar"):
        ctx.avisar(0.75, "Escribiendo la fecha en los metadatos")
        orden = [sys.executable, str(FOTOS), "embed-date", str(copia), "--execute"]
        if ctx.p("nombre_manda"):
            orden.append("--trust-name")
        correr(orden, timeout=2 * HORAS, entorno={"NO_COLOR": "1"}, mensaje="No se pudo escribir la fecha")
    return Resultado([copia], mensajes=[f"{len(medios)} archivo(s) en {copia.name}"])
