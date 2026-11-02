"""Raphi Studio: el escritorio nativo de Raphi en la familia de los studios (QML + Kirigami sobre gui-comun 2.7).

Revisa R4 sin volver a la duplicación (`docs/decisiones.md`, R9 del 2026-10-31 y la entrada del 2026-11-02): sus
pantallas no se escriben a mano; las opciones de cada herramienta se arman de la ficha del motor (`PaginaFormulario`
del marco), como los formularios de la web. La ventana corre con el Python del sistema (el PySide6 y el Kirigami de
apt) y el motor corre como proceso con el `.venv` del repo (`corredor.py`), que ya tiene pikepdf, PyMuPDF, Pillow y lo
demás (`docs/rediseno.md` S1).

`gui_comun` se localiza instalado (pip) o por `GUI_COMUN_DIR` (la carpeta del repo `gui-comun`, que `run.sh` y
`escritorio/__main__.py` ponen cuando está): nunca subiendo carpetas, porque Raphi corre fuera del espacio de trabajo.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "Raphi Studio"
ORG_NAME = "achalma"
VARIABLE_GUI_COMUN = "GUI_COMUN_DIR"


def hay_gui_comun() -> bool:
    """¿Está `gui_comun`? Instalado, o en la carpeta que diga `GUI_COMUN_DIR` (se añade al final del `sys.path`)."""
    try:
        import gui_comun  # noqa: F401
        return True
    except ImportError:
        pass
    carpeta = os.environ.get(VARIABLE_GUI_COMUN, "").strip()
    if carpeta and (Path(carpeta) / "gui_comun").is_dir():
        sys.path.append(carpeta)
        return True
    return False
