"""Lo que comparten las operaciones: rangos de páginas, procesos externos, LibreOffice aislado y tamaños."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

from raphi.motor.base import ErrorOperacion

# --- rangos de páginas -----------------------------------------------------------------------------------------


def interpretar_paginas(texto: str | None, total: int, vacio_es_todas: bool = True) -> list[int]:
    """«1-5,7,10-z» → índices desde 0 (en el orden escrito, sin repetir). `z` es la última; «-3» son las tres últimas.

    Vacío: todas (o ninguna, con `vacio_es_todas=False`)."""
    texto = (texto or "").strip().lower().replace(" ", "")
    if not texto:
        return list(range(total)) if vacio_es_todas else []
    salida: list[int] = []

    def numero(t: str) -> int:
        if t in ("z", "fin", "ultima", "última"):
            return total
        if not t.isdigit():
            raise ErrorOperacion(f"Página no válida: «{t}». Use números, rangos (3-7) y «z» para la última.")
        return int(t)

    for trozo in texto.split(","):
        if not trozo:
            continue
        if re.fullmatch(r"-\d+", trozo):
            n = int(trozo[1:])
            rango = range(max(1, total - n + 1), total + 1)
        elif "-" in trozo:
            a, b = trozo.split("-", 1)
            ia, ib = numero(a or "1"), numero(b or "z")
            rango = range(ia, ib + 1) if ia <= ib else range(ia, ib - 1, -1)
        else:
            rango = [numero(trozo)]
        for n in rango:
            if not 1 <= n <= total:
                raise ErrorOperacion(f"La página {n} no existe: el documento tiene {total}.")
            if n - 1 not in salida:
                salida.append(n - 1)
    return salida


# --- procesos --------------------------------------------------------------------------------------------------


def correr(orden: list[str], *, timeout: int = 600, entorno: dict | None = None, cwd: Path | None = None,
           mensaje: str = "") -> subprocess.CompletedProcess:
    """Un programa externo con tope de tiempo; un fallo se vuelve ErrorOperacion con lo último de su stderr."""
    env = {**os.environ, **(entorno or {})}
    try:
        r = subprocess.run(orden, capture_output=True, text=True, timeout=timeout, env=env, cwd=cwd)
    except FileNotFoundError as e:
        raise ErrorOperacion(f"Falta el programa «{orden[0]}».") from e
    except subprocess.TimeoutExpired as e:
        raise ErrorOperacion(f"«{orden[0]}» tardó más de {timeout} s y se detuvo.") from e
    if r.returncode != 0:
        detalle = (r.stderr or r.stdout or "").strip().splitlines()[-3:]
        raise ErrorOperacion((mensaje or f"«{orden[0]}» falló (código {r.returncode})")
                             + (": " + " · ".join(detalle) if detalle else "."))
    return r


SOFFICE_TIMEOUT = int(os.environ.get("RAPHI_SOFFICE_TIMEOUT", "300"))


def soffice(entrada: Path, formato: str, carpeta: Path, filtro_entrada: str = "") -> Path:
    """LibreOffice sin cabeza con un PERFIL PROPIO por llamada (el compartido se corrompe si corren dos a la vez) y
    comprobando que el archivo esperado exista (soffice devuelve 0 aunque no convierta: documentos protegidos)."""
    perfil = carpeta / ".perfil-libreoffice"
    orden = ["soffice", f"-env:UserInstallation=file://{perfil}", "--headless", "--norestore"]
    if filtro_entrada:
        orden.append(f"--infilter={filtro_entrada}")
    orden += ["--convert-to", formato, "--outdir", str(carpeta), str(entrada)]
    correr(orden, timeout=SOFFICE_TIMEOUT, mensaje=f"LibreOffice no pudo convertir {entrada.name}")
    shutil.rmtree(perfil, ignore_errors=True)
    extension = "." + formato.split(":", 1)[0]
    esperado = carpeta / f"{entrada.stem}{extension}"
    if not esperado.is_file() or esperado.stat().st_size == 0:
        raise ErrorOperacion(f"LibreOffice no produjo {esperado.name} (¿documento protegido o dañado?).")
    return esperado


# --- tamaños ---------------------------------------------------------------------------------------------------


def tamano_legible(n: int | float) -> str:
    n = float(n)
    for unidad in ("B", "KB", "MB", "GB"):
        if n < 1024 or unidad == "GB":
            return f"{n:.0f} {unidad}" if unidad == "B" else f"{n:.1f} {unidad}"
        n /= 1024
    return f"{n:.1f} GB"


def mover(origen: Path, destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(origen), str(destino))
    return destino


POSICIONES = (("arriba-izquierda", "Arriba a la izquierda"), ("arriba-centro", "Arriba al centro"),
              ("arriba-derecha", "Arriba a la derecha"), ("abajo-izquierda", "Abajo a la izquierda"),
              ("abajo-centro", "Abajo al centro"), ("abajo-derecha", "Abajo a la derecha"), ("centro", "Al centro"))


def punto_en(rect, posicion: str, ancho: float, alto: float, margen: float = 28) -> tuple[float, float]:
    """La esquina superior izquierda de una caja de `ancho`×`alto` en la `posicion` de la página (puntos PDF)."""
    x0, y0, x1, y1 = rect.x0, rect.y0, rect.x1, rect.y1
    v, _, h = posicion.partition("-") if posicion != "centro" else ("centro", "", "centro")
    x = {"izquierda": x0 + margen, "centro": (x0 + x1 - ancho) / 2, "derecha": x1 - margen - ancho}[h or "centro"]
    y = {"arriba": y0 + margen, "centro": (y0 + y1 - alto) / 2, "abajo": y1 - margen - alto}[v]
    return x, y


def color_rgb(texto: str) -> tuple[float, float, float]:
    t = (texto or "#000000").lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", t):
        raise ErrorOperacion(f"Color no válido: «{texto}» (use #RRGGBB).")
    return tuple(int(t[i:i + 2], 16) / 255 for i in (0, 2, 4))
