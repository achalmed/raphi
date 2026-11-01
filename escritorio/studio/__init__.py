"""Raphi Studio: el escritorio nativo de Raphi en la familia de los studios (Filesystem, Git, Quarto, LaTeX).

Revisa R4 sin volver a la duplicación (`docs/decisiones.md`, 2026-10-31): sus páginas no se escriben a mano; se arman
de las fichas del motor, como los formularios de la web. Usa el marco común de los studios, `gui_comun`, que vive en
el paquete público `gui-comun` (requirements.txt), o el repo `gui-comun/` del espacio de trabajo; `hay_gui_comun()`
lo busca. Sin él, `raphi` abre la ventana web de siempre.
"""
from __future__ import annotations

import sys
from pathlib import Path


def hay_gui_comun() -> bool:
    """¿Está `gui_comun`? Instalado (requirements.txt lo trae del repo público) o, en el espacio de trabajo, el repo
    `gui-comun/` subiendo carpetas."""
    try:
        import gui_comun  # noqa: F401
        return True
    except ImportError:
        pass
    d = Path(__file__).resolve().parent
    while d != d.parent and not (d / "gui-comun" / "gui_comun").is_dir():
        d = d.parent
    if not (d / "gui-comun" / "gui_comun").is_dir():
        return False
    sys.path.append(str(d / "gui-comun"))
    return True
