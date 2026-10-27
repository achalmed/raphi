"""El servidor de Raphi ESCRITORIO: la misma API y la misma web, para una sola persona en su máquina.

Lo arranca la ventana del escritorio (`escritorio/`, R4) en 127.0.0.1 y un puerto libre, con una ficha de un solo
uso (`RAPHI_FICHA`): sin ella nadie más (otra página del navegador, otro usuario de la máquina) puede usar la API.
La ventana pone esa ficha donde la cáscara mínima de Tiqsi guarda la sesión (`tiqsi_token`), así que la web es la
misma que en Qillqa o sola, sin pantalla de inicio de sesión.

Lo propio del escritorio (`RAPHI_MODO=escritorio`): archivos del disco por su ruta (`POST /api/raphi/locales`) y
trabajos que escriben junto al original o en una carpeta elegida. La base es SQLite en `RAPHI_DIR`.

    RAPHI_FICHA=$(python -c 'import secrets;print(secrets.token_urlsafe(32))') \\
      .venv/bin/python -m raphi.escritorio --puerto 0
"""
from __future__ import annotations

import argparse
import hmac
import os
import socket
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

os.environ["RAPHI_MODO"] = "escritorio"

from fastapi import FastAPI, Header, HTTPException  # noqa: E402

from raphi import config as configuracion  # noqa: E402

configuracion.recargar()

from tiqsi import Anfitrion  # noqa: E402
from tiqsi import puertos as marcadores  # noqa: E402

from raphi.manifiesto import MANIFIESTO  # noqa: E402

WEB_REPO = Path(__file__).resolve().parents[1] / "web" / "dist"
PERSONA = SimpleNamespace(id=1, rol="administrador", nombre=os.environ.get("USER", "yo").capitalize(), cargo="")


def crear_app(ficha: str, web: Path | None = None) -> FastAPI:
    if len(ficha) < 24:
        raise ValueError("La ficha del escritorio debe tener al menos 24 caracteres.")

    async def usuario_actual(authorization: str = Header(default="")) -> SimpleNamespace:
        dada = authorization.removeprefix("Bearer ").strip()
        if not hmac.compare_digest(dada.encode(), ficha.encode()):
            raise HTTPException(401, "Raphi escritorio: falta la ficha de esta sesión.")
        return PERSONA

    async def persona(_ident: int) -> dict:
        return {"nombre": PERSONA.nombre, "cargo": ""}

    identidad = SimpleNamespace(usuario_actual=usuario_actual, solo_administrador=usuario_actual, persona=persona,
                                cuenta=lambda _i: None, cuentas=lambda: [], de_ficha=None)
    anfitrion = Anfitrion("raphi-escritorio", puertos={"identidad.v1": identidad},
                          dependencias={marcadores.usuario_actual: usuario_actual,
                                        marcadores.solo_administrador: usuario_actual})
    anfitrion.registrar([MANIFIESTO])
    anfitrion.activar()

    @asynccontextmanager
    async def ciclo(_app):
        await anfitrion.arrancar()
        yield
        await anfitrion.detener()

    app = FastAPI(title="Raphi escritorio", lifespan=ciclo)

    @app.get("/api/health")
    async def salud() -> dict:
        return {"api": "ok", "anfitrion": "raphi-escritorio"}

    anfitrion.montar(app)
    web = web or (WEB_REPO if WEB_REPO.is_dir() else None)
    if web and Path(web).is_dir():
        from fastapi.staticfiles import StaticFiles
        app.mount("/", StaticFiles(directory=str(web), html=True), name="web")
    app.state.anfitrion = anfitrion
    return app


def puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main(argv: list[str] | None = None) -> int:
    import uvicorn
    ap = argparse.ArgumentParser(description="El servidor local de Raphi escritorio.")
    ap.add_argument("--puerto", type=int, default=0, help="0 = uno libre (se imprime al arrancar)")
    ap.add_argument("--web", type=Path, default=None)
    a = ap.parse_args(argv)
    ficha = os.environ.get("RAPHI_FICHA")
    if not ficha:
        raise SystemExit("Falta RAPHI_FICHA (la pone la ventana del escritorio).")
    puerto = a.puerto or puerto_libre()
    print(f"RAPHI_PUERTO={puerto}", flush=True)
    uvicorn.run(crear_app(ficha, a.web), host="127.0.0.1", port=puerto, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
