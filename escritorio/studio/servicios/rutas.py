"""escritorio/studio/servicios/rutas.py — dónde está cada cosa: el repo, el intérprete del motor (el `.venv` del repo,
o `RAPHI_MOTOR_PYTHON`), el corredor y `core/env.py` cuando el espacio de trabajo está (`gui_comun.rutas`; sin él, el
repo se basta). Ninguna ruta de la máquina aquí."""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]          # raphi (escritorio/studio/servicios/rutas.py)
STUDIO = REPO / "escritorio" / "studio"
CORREDOR = STUDIO / "corredor.py"
VARIABLE_MOTOR = "RAPHI_MOTOR_PYTHON"


def venv_dir() -> Path:
    return REPO / ".venv"


def interprete_motor() -> str:
    """El Python con el que corre el motor (el corredor): `RAPHI_MOTOR_PYTHON`, el `.venv` del repo o, sin él, el
    Python de esta ventana (las operaciones que necesiten pikepdf o Pillow fallarán y la ventana dice qué crear)."""
    dicho = os.environ.get(VARIABLE_MOTOR, "").strip()
    if dicho and Path(dicho).is_file():
        return dicho
    venv = venv_dir() / "bin" / "python"
    return str(venv) if venv.is_file() else sys.executable


def hay_venv() -> bool:
    return (venv_dir() / "bin" / "python").is_file()


def orden_crear_venv() -> str:
    """La orden que crea el entorno del motor (se muestra, no se corre sola): install.sh lo hace todo."""
    return f"{REPO / 'install.sh'}   # crea {venv_dir()} con /usr/bin/python3 y pip install -r requirements.txt"


def core_env():
    """El módulo core/env.py del espacio de trabajo, o None fuera de él."""
    try:
        from gui_comun import rutas
        return rutas.core_env()
    except Exception:       # noqa: BLE001
        return None


def carpeta_descargas() -> Path:
    env = core_env()
    for nombre in ("DESCARGAS_DIR", "DOWNLOADS_DIR"):
        if env is not None and getattr(env, nombre, None):
            return Path(getattr(env, nombre))
    xdg = Path.home() / ".config" / "user-dirs.dirs"
    if xdg.is_file():
        for linea in xdg.read_text(encoding="utf-8", errors="ignore").splitlines():
            if linea.startswith("XDG_DOWNLOAD_DIR="):
                return Path(os.path.expandvars(linea.split("=", 1)[1].strip().strip('"')))
    return Path.home() / "Descargas"


def programa(nombre: str) -> str | None:
    return shutil.which(nombre)


def relativa(ruta: Path | str) -> str:
    """Una ruta corta para mostrarla: relativa a la carpeta de inicio (`~/…`) si cae dentro."""
    ruta = Path(ruta)
    try:
        return "~/" + ruta.relative_to(Path.home()).as_posix()
    except ValueError:
        return str(ruta)
