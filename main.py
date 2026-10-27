#!/usr/bin/env python3
# main.py — Raphi escritorio (PySide6; antes DocFlow Studio): entrada según el patrón (FS3, 2026-09-07). Equivale a `python -m studio` / run.sh.
# Config: studio/core/settings.py (QSettings) y studio/core/paths.py; interfaz: studio/ui; backends: backends/*.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from studio.app import main   # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
