"""Raphi SOLA: la web con cuentas locales, sin Qillqa, con el anfitrión mínimo de Tiqsi.

    RAPHI_DIR=… JWT_SECRET=<32 o más caracteres> .venv/bin/uvicorn raphi.sola:app --port 8040

Las cuentas viven en `RAPHI_CUENTAS` (por omisión `<RAPHI_DIR>/cuentas.json`) y se crean con
`python -m tiqsi.minimo cuenta <archivo> <usuario> --rol administrador --nombre …`. La página es `RAPHI_WEB` (por
omisión `web/dist` del repo, si está construida). Sin Qillqa no hay campana ni objetos de otros módulos: todo lo demás
funciona igual.
"""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("RAPHI_MODO", "sola")

from raphi import config as configuracion  # noqa: E402

configuracion.recargar()
if not os.environ.get("JWT_SECRET"):
    raise SystemExit("Raphi sola necesita su secreto: JWT_SECRET (32 o más caracteres; firma las sesiones).")

from tiqsi.minimo import crear_app  # noqa: E402

from raphi.manifiesto import MANIFIESTO  # noqa: E402

WEB_REPO = Path(__file__).resolve().parents[1] / "web" / "dist"

app = crear_app([MANIFIESTO], nombre="Raphi", secreto=os.environ["JWT_SECRET"],
                cuentas=os.environ.get("RAPHI_CUENTAS") or configuracion.config.dir / "cuentas.json",
                web=os.environ.get("RAPHI_WEB") or (WEB_REPO if WEB_REPO.is_dir() else None))
