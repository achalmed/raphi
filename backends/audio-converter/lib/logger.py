"""script_audio_converter/lib/logger.py — envoltorio (FS2, 2026-09-07): el logger vive en core/py-common/logger.py."""
from __future__ import annotations

import importlib.util
import pathlib

_p = pathlib.Path(__file__).resolve()
while _p != _p.parent and not (_p / "core" / "py-common" / "logger.py").exists():
    _p = _p.parent
_s = importlib.util.spec_from_file_location("core_logger", _p / "core" / "py-common" / "logger.py")
_core = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_core)

import config


def setup_logger(name, verbose=False, log_file=None):
    return _core.configurar(name, verbose, log_file, color=getattr(config, "USE_COLOR", None),
                            colores=getattr(config, "LEVEL_COLORS", None), reset=getattr(config, "ANSI_RESET", _core.RESET))
