"""tests/studio/conftest.py — utilidades de las pruebas de Raphi Studio (fase 5 QML, 2026-11-02).

El temporal va al disco (XDG_CACHE_HOME), no a /tmp (tmpfs: es RAM). Nada toca los archivos del usuario: cada prueba
parte de los archivos de muestra de `escritorio/studio/muestra.py` (un PDF, un PNG, unos subtítulos, un Markdown y una
carpeta, escritos a mano) en una carpeta temporal. El motor corre, como en la ventana, con el `.venv` del repo
(`RAPHI_MOTOR_PYTHON` o `<repo>/.venv/bin/python`); sin él, lo que lo necesita se salta. Nunca descargan ni transcriben.

Dos clases de prueba:
- en proceso (servicios, controladores): con el binding del Python que corre pytest; QSettings apunta a un temporal;
- en un proceso hijo (cada QML, la ventana entera, `--smoke`): con el Python del sistema (/usr/bin/python3), el único
  cuyo Qt trae Kirigami, y HOME, XDG_CONFIG_HOME, XDG_CACHE_HOME temporales. `gui_comun` llega instalado o por
  `GUI_COMUN_DIR` (tests/run.sh lo pone si el repo gui-comun está al lado).

    tests/run.sh            # = python3 -m pytest tests/studio --basetemp ~/.cache/pytest/raphi-studio -p no:cacheprovider
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
STUDIO = REPO / "escritorio" / "studio"
BASETEMP = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "pytest" / "raphi-studio" / "basetemp"

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
if "GUI_COMUN_DIR" not in os.environ and (REPO.parent / "gui-comun" / "gui_comun").is_dir():
    os.environ["GUI_COMUN_DIR"] = str(REPO.parent / "gui-comun")

from escritorio.studio import hay_gui_comun  # noqa: E402
from escritorio.studio import muestra as muestra_mod  # noqa: E402

HAY_GUI_COMUN = hay_gui_comun()
HAY_BINDING = importlib.util.find_spec("PySide6") is not None or importlib.util.find_spec("PyQt6") is not None
MOTOR = os.environ.get("RAPHI_MOTOR_PYTHON") or (str(REPO / ".venv" / "bin" / "python") if (REPO / ".venv" / "bin" / "python").is_file() else "")
requiere_binding = pytest.mark.skipif(not (HAY_BINDING and HAY_GUI_COMUN), reason="sin PySide6/PyQt6 o sin gui_comun")
requiere_motor = pytest.mark.skipif(not MOTOR, reason="sin el .venv del repo (el motor): install.sh lo crea")


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    if config.option.basetemp:
        return
    args = [Path(a.split("::")[0]).resolve() for a in (config.args or [])]
    if args and all(REPO in a.parents or a == REPO for a in args):
        BASETEMP.parent.mkdir(parents=True, exist_ok=True)
        config.option.basetemp = str(BASETEMP)


def _python_del_sistema() -> str | None:
    candidato = Path("/usr/bin/python3")
    if not candidato.is_file() or not HAY_GUI_COMUN:
        return None
    r = subprocess.run([str(candidato), "-c", "import PySide6.QtQml"], capture_output=True, text=True)
    return str(candidato) if r.returncode == 0 else None


PYTHON_SISTEMA = _python_del_sistema()
requiere_sistema = pytest.mark.skipif(PYTHON_SISTEMA is None, reason="sin PySide6 con QML en /usr/bin/python3 (Kirigami)")


@pytest.fixture(scope="session")
def muestra_sesion(tmp_path_factory):
    return muestra_mod.crear(tmp_path_factory.mktemp("muestra") / "archivos")


@pytest.fixture
def muestra(tmp_path):
    """Archivos de muestra nuevos por prueba (para los procesos hijos y para lo que escribe)."""
    return muestra_mod.crear(tmp_path / "archivos")


@pytest.fixture
def ajustes_temporales(tmp_path, monkeypatch):
    from gui_comun.qt import QSettings
    QSettings.setPath(QSettings.Format.NativeFormat, QSettings.Scope.UserScope, str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "datos"))
    if MOTOR:
        monkeypatch.setenv("RAPHI_MOTOR_PYTHON", MOTOR)
    return tmp_path


def entorno_gui(tmp_path: Path, muestra, **extra: str) -> dict:
    env = dict(os.environ)
    env.update({"QT_QPA_PLATFORM": "offscreen", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(REPO)})
    env.update(muestra.entorno)
    if MOTOR:
        env["RAPHI_MOTOR_PYTHON"] = MOTOR
    env["RAPHI_STUDIO_MUESTRA"] = str(muestra.raiz)
    env.update(extra)
    return env


def correr_python(guion: str, env: dict, *args: str, plazo: int = 180) -> subprocess.CompletedProcess:
    return subprocess.run([PYTHON_SISTEMA or sys.executable, "-c", guion, str(REPO), *args], env=env, capture_output=True, text=True, timeout=plazo)


@pytest.fixture(scope="session")
def app():
    if not (HAY_BINDING and HAY_GUI_COMUN):
        pytest.skip("sin binding o sin gui_comun")
    from gui_comun.qt import QGuiApplication
    QGuiApplication.setOrganizationName("raphi-studio-pruebas")
    QGuiApplication.setApplicationName("raphi-studio-pruebas")
    instancia = QGuiApplication.instance() or QGuiApplication([sys.argv[0]])
    yield instancia
