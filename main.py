#!/usr/bin/env python3
# main.py — Raphi escritorio: entrada según el patrón (FS3, 2026-09-07). Equivale a `python -m escritorio` y a `raphi`.
# La ventana muestra la web (web/dist) servida por raphi.escritorio; el motor y la CLI están en raphi/ (python -m raphi).
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from escritorio.ventana import main   # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
