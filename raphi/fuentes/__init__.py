"""Fuentes: de dónde salen los PDF de una operación de inventario.

- «archivos»: los archivos y carpetas elegidos (una carpeta se recorre entera; cada carpeta es un grupo);
- «hub»: los blogs del hub del espacio de trabajo, por `core/env.py` y el registro `<hub>/_pubs/pubs.yml`
  (`core/py-common/pubs.py`), como hacía `page-counter`. Fuera del espacio de trabajo esta fuente no existe: la demo
  pública la excluye y `disponibles()` no la ofrece.
"""
from __future__ import annotations

from pathlib import Path

from raphi.motor.base import ErrorOperacion

Grupo = tuple[str, list[tuple[Path | None, Path]]]     # (nombre del grupo, [(raíz para la ruta relativa, pdf)])


def disponibles() -> list[str]:
    from raphi.fuentes import hub
    return ["archivos"] + (["hub"] if hub.hay() else [])


def agrupar(fuente: str, entradas: list[Path], solo_index: bool = False, blogs: list[str] | None = None) -> list[Grupo]:
    if fuente == "hub":
        from raphi.fuentes import hub
        return hub.grupos(solo_index=solo_index, blogs=blogs or [])
    if fuente != "archivos":
        raise ErrorOperacion(f"Fuente desconocida: {fuente}")
    if not entradas:
        raise ErrorOperacion("Elija archivos o carpetas.")
    sueltos: list[tuple[Path | None, Path]] = []
    grupos: list[Grupo] = []
    for e in entradas:
        if e.is_dir():
            pdfs = sorted(p for p in e.rglob("*.pdf" if not solo_index else "index.pdf") if p.is_file())
            grupos.append((e.name, [(e, p) for p in pdfs]))
        elif e.suffix.lower() == ".pdf" and (not solo_index or e.name == "index.pdf"):
            sueltos.append((e.parent, e))
    if sueltos:
        grupos.insert(0, ("archivos", sueltos))
    return [g for g in grupos if g[1]]
