"""La base propia de Raphi: los archivos que se le dieron, los trabajos y su bandeja de salida.

Con el mismo código en SQLite (escritorio, sola, pruebas) y en PostgreSQL (dentro de Qillqa). Las tablas llevan el
prefijo `raphi_` para que se reconozcan en una base compartida; no hay claves foráneas hacia nadie más.
"""
from __future__ import annotations

from sqlalchemy import JSON, BigInteger, Boolean, Column, DateTime, Float, Integer, MetaData, String, Table, Text, func
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from tiqsi.bandeja_sql import tabla_bandeja

METADATA = MetaData()

ARCHIVOS = Table(
    "raphi_archivos", METADATA,
    Column("id", String(32), primary_key=True),
    Column("cuenta", Integer, nullable=False, index=True),
    Column("nombre", String(255), nullable=False),
    Column("ruta", Text, nullable=False),
    Column("bytes", BigInteger, nullable=False, default=0),
    Column("local", Boolean, nullable=False, default=False),      # escritorio: un archivo del disco, no una copia
    Column("creado_en", DateTime(timezone=True), server_default=func.now(), index=True),
)

TRABAJOS = Table(
    "raphi_trabajos", METADATA,
    Column("id", String(32), primary_key=True),
    Column("cuenta", Integer, nullable=False, index=True),
    Column("operacion", String(60), nullable=False),               # el id de la operación o «receta:<id>»
    Column("titulo", String(200), nullable=False, default=""),
    Column("params", JSON, nullable=False, default=dict),
    Column("archivos", JSON, nullable=False, default=list),        # ids de raphi_archivos
    Column("destino", Text, nullable=False, default=""),           # escritorio: «junto» o una carpeta; si no, vacío
    Column("simular", Boolean, nullable=False, default=False),
    Column("estado", String(20), nullable=False, default="pendiente", index=True),
    Column("progreso", Float, nullable=False, default=0.0),
    Column("mensaje", Text, nullable=False, default=""),
    Column("informe", JSON, nullable=True),
    Column("salidas", JSON, nullable=False, default=list),         # rutas de las salidas
    Column("referencia", String(120), nullable=False, default=""),  # «modulo:tipo:id» de quien lo pidió, si alguien
    Column("creado_en", DateTime(timezone=True), server_default=func.now(), index=True),
    Column("terminado_en", DateTime(timezone=True), nullable=True),
)

BANDEJA = tabla_bandeja(METADATA, "raphi_bandeja")

ESTADOS = ("pendiente", "en_curso", "hecho", "parcial", "fallido", "cancelado")

_motor: AsyncEngine | None = None
_url: str = ""
Sesion: async_sessionmaker | None = None


def conectar(url: str) -> async_sessionmaker:
    global _motor, Sesion, _url
    _url = url
    _motor = create_async_engine(url, pool_pre_ping=True)
    Sesion = async_sessionmaker(_motor, expire_on_commit=False)
    return Sesion


def sesion():
    if Sesion is None:
        raise RuntimeError("La base de Raphi no está conectada (raphi.db.preparar).")
    return Sesion()


async def preparar(url: str) -> None:
    """La base si falta (PostgreSQL), sus tablas y nada más: el esquema es aditivo."""
    from tiqsi.sql import crear_base_si_falta
    if url.startswith("sqlite") and ":///" in url:
        from pathlib import Path
        Path(url.split(":///", 1)[1]).parent.mkdir(parents=True, exist_ok=True)
    await crear_base_si_falta(url)
    if Sesion is None or _url != url:
        await cerrar()
        conectar(url)
    async with _motor.begin() as c:
        await c.run_sync(METADATA.create_all)


async def cerrar() -> None:
    global _motor, Sesion
    if _motor is not None:
        await _motor.dispose()
    _motor, Sesion = None, None


class _FabricaPerezosa:
    """La bandeja necesita su fábrica de sesiones al declararse el manifiesto, antes de que la base se conecte."""

    def __call__(self):
        return sesion()


fabrica = _FabricaPerezosa()
