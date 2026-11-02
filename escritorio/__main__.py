"""`python -m escritorio [--web] [archivos…]`: abre Raphi Studio, el escritorio nativo de la familia de los studios (o le
manda los archivos si ya está abierto). Con `--web`, la ventana que muestra la web.

Raphi Studio corre con el Python del sistema (`/usr/bin/python3`: su PySide6 es el que carga Kirigami), mientras este
módulo corre en el `.venv` del repo (`raphi`, run.sh): aquí se relanza al del sistema diciéndole dónde está este
intérprete (`RAPHI_MOTOR_PYTHON`, con el que corre el motor) y dónde está `gui_comun` (`GUI_COMUN_DIR`: instalado en el
`.venv` como editable, o el repo de al lado). Si el Python del sistema no trae PySide6 con QML, se abre la ventana web."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PYTHON_SISTEMA = "/usr/bin/python3"


def _carpeta_gui_comun() -> str:
    try:
        import gui_comun
        return str(Path(gui_comun.__file__).resolve().parents[1])
    except ImportError:
        vecino = RAIZ.parent / "gui-comun"
        return str(vecino) if (vecino / "gui_comun").is_dir() else ""


def _es_python_sistema() -> bool:
    """¿Este intérprete es el del sistema y no el de un `.venv`? El `python` de un `.venv` es un enlace a
    `/usr/bin/python3`: resolver la ruta no basta (los dos dan `/usr/bin/python3.14`) y, si se confunden, la ventana
    carga el PySide6 de pip del `.venv`, que no trae Kirigami."""
    return sys.prefix == sys.base_prefix and Path(sys.executable).resolve() == Path(PYTHON_SISTEMA).resolve()


def _sistema_sirve() -> bool:
    if not Path(PYTHON_SISTEMA).is_file():
        return False
    r = subprocess.run([PYTHON_SISTEMA, "-c", "import PySide6.QtQml, PySide6.QtQuick"], capture_output=True)
    return r.returncode == 0


def main(argv: list[str]) -> int:
    if "--web" in argv:
        from escritorio.ventana import main as web
        return web([a for a in argv if a != "--web"])
    carpeta = _carpeta_gui_comun()
    if not carpeta or not _sistema_sirve():
        print("raphi: sin gui_comun o sin el PySide6 del sistema (Kirigami): se abre la ventana web.", file=sys.stderr)
        from escritorio.ventana import main as web
        return web(argv)
    if _es_python_sistema():
        from escritorio.studio.aplicacion import main as studio
        return studio(argv)
    entorno = {**os.environ, "RAPHI_MOTOR_PYTHON": sys.executable, "GUI_COMUN_DIR": carpeta,
               "PYTHONPATH": str(RAIZ) + (os.pathsep + os.environ["PYTHONPATH"] if os.environ.get("PYTHONPATH") else "")}
    os.execve(PYTHON_SISTEMA, [PYTHON_SISTEMA, "-m", "escritorio.studio", *argv], entorno)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
