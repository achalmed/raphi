"""Resolución de rutas del proyecto y de los backends.

Única fuente de verdad para localizar los ejecutables de backend.
Los backends viven bajo backends/ de la raíz del repo; el usuario puede
sobreescribir cada ruta desde Sistema → Ajustes (persisten en QSettings).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

# raíz del repo (dos niveles sobre este archivo)
STUDIO_ROOT = Path(__file__).resolve().parents[2]
BACKENDS_DIR = STUDIO_ROOT / "backends"

DOCFLOW_BIN = BACKENDS_DIR / "docflow" / "bin" / "docflow"
PDFSUITE_MAIN = BACKENDS_DIR / "pdf-suite" / "main.sh"
PAGECOUNTER_DIR = BACKENDS_DIR / "page-counter"

# Estado de la app (logs, sesiones) según XDG
_STATE_BASE = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
STATE_DIR = _STATE_BASE / "raphi"
STATE_DIR_ANTERIOR = _STATE_BASE / "docflow-studio"   # nombre anterior de la app; ensure_state_dir lo mueve
LOG_FILE = STATE_DIR / "studio.log"

# Config TOML de docflow (la gestiona docflow config init/show)
DOCFLOW_CONFIG_TOML = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "docflow" / "config.toml"


def ensure_state_dir() -> None:
    if STATE_DIR_ANTERIOR.is_dir() and not STATE_DIR.exists():
        STATE_DIR_ANTERIOR.rename(STATE_DIR)   # el registro del nombre anterior sigue con la app
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def docflow_cmd(settings=None) -> list[str]:
    """Comando base para invocar docflow (respeta override del usuario)."""
    binario = _override(settings, "backends/docflow", DOCFLOW_BIN)
    return ["bash", str(binario)]


def pdfsuite_cmd(settings=None) -> list[str]:
    """Comando base para invocar pdf-suite (respeta override del usuario)."""
    binario = _override(settings, "backends/pdfsuite", PDFSUITE_MAIN)
    return ["bash", str(binario)]


def pagecounter_dir(settings=None) -> Path:
    return Path(_override(settings, "backends/pagecounter", PAGECOUNTER_DIR))


def _override(settings, key: str, default: Path) -> Path:
    if settings is not None:
        valor = settings.value(key, "")
        if valor:
            return Path(str(valor)).expanduser()
    return default


def missing_backends(settings=None) -> list[str]:
    """Backends cuya ruta no existe (para avisar al arrancar)."""
    faltan = []
    if not Path(docflow_cmd(settings)[1]).is_file():
        faltan.append("docflow")
    if not Path(pdfsuite_cmd(settings)[1]).is_file():
        faltan.append("pdf-suite")
    if not (pagecounter_dir(settings) / "config.py").is_file():
        faltan.append("page-counter")
    return faltan


def which_or_none(tool: str) -> str | None:
    return shutil.which(tool)
