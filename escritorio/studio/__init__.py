"""Raphi Studio: el escritorio nativo de Raphi en la familia de los studios (Filesystem, Git, Quarto, LaTeX).

Revisa R4 sin volver a la duplicación (`docs/decisiones.md`, 2026-10-31): sus páginas no se escriben a mano; se arman
de las fichas del motor, como los formularios de la web. Usa el marco común de los studios, `gui_comun`, que vive en
`core/py-common` del espacio de trabajo; `hay_gui_comun()` lo busca subiendo carpetas (como los otros studios). Fuera
del espacio de trabajo (Raphi instalado solo) no está: `raphi` abre entonces la ventana web de siempre.
"""
from __future__ import annotations

import sys
from pathlib import Path


def hay_gui_comun() -> bool:
    d = Path(__file__).resolve().parent
    while d != d.parent and not (d / "core" / "py-common" / "gui_comun").is_dir():
        d = d.parent
    comun = d / "core" / "py-common"
    if not (comun / "gui_comun").is_dir():
        return False
    if str(comun) not in sys.path:
        sys.path.append(str(comun))
    return True
