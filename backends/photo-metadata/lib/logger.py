"""scripts_for_linux/scripts_photo_metadata_suite/lib/logger.py — envoltorio (FS2, 2026-09-07): el logger vive en core/py-common/logger.py."""
from __future__ import annotations

import importlib.util
import pathlib

_p = pathlib.Path(__file__).resolve()
while _p != _p.parent and not (_p / "core" / "py-common" / "logger.py").exists():
    _p = _p.parent
_s = importlib.util.spec_from_file_location("core_logger", _p / "core" / "py-common" / "logger.py")
_core = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_core)


def setup_logger(name, verbose=False, log_file=None):
    return _core.configurar(name, verbose, log_file)
