"""La configuración de Raphi como servicio, por variables de entorno (nada de rutas de máquina en el código).

| variable | por omisión | para qué |
|---|---|---|
| `RAPHI_DIR` | `$XDG_DATA_HOME/raphi` | archivos subidos, salidas de los trabajos y la base SQLite |
| `RAPHI_DATABASE_URL` | `sqlite+aiosqlite:///<RAPHI_DIR>/raphi.db` | su base (PostgreSQL dentro de Qillqa) |
| `RAPHI_MODO` | `modulo` | `modulo` (dentro de un anfitrión) · `sola` (con cuentas) · `escritorio` (una persona, archivos locales) |
| `RAPHI_CONCURRENCIA` | `1` | trabajos a la vez (el OCR es pesado: en la máquina de producción, 1) |
| `RAPHI_RETENCION_HORAS` | `24` | a cuántas horas se borran los archivos subidos y las salidas |
| `RAPHI_TOPE_SUBIDA_MB` | `500` | el tamaño máximo de un archivo subido |
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    dir: Path
    database_url: str
    modo: str
    concurrencia: int
    retencion_horas: float
    tope_subida_mb: int

    @property
    def escritorio(self) -> bool:
        return self.modo == "escritorio"

    @property
    def subidos(self) -> Path:
        return self.dir / "subidos"

    @property
    def trabajos(self) -> Path:
        return self.dir / "trabajos"


def leer() -> Config:
    base = Path(os.environ.get("RAPHI_DIR") or Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "raphi")
    modo = os.environ.get("RAPHI_MODO", "modulo")
    if modo not in ("modulo", "sola", "escritorio"):
        raise SystemExit(f"RAPHI_MODO no válido: {modo} (modulo · sola · escritorio)")
    return Config(dir=base, database_url=os.environ.get("RAPHI_DATABASE_URL") or f"sqlite+aiosqlite:///{base / 'raphi.db'}",
                  modo=modo, concurrencia=max(1, int(os.environ.get("RAPHI_CONCURRENCIA", "1"))),
                  retencion_horas=float(os.environ.get("RAPHI_RETENCION_HORAS", "24")),
                  tope_subida_mb=int(os.environ.get("RAPHI_TOPE_SUBIDA_MB", "500")))


config = leer()


def recargar() -> Config:
    """Para las pruebas y los modos que fijan su entorno antes de arrancar."""
    global config
    config = leer()
    return config
