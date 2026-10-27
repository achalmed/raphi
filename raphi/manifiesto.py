"""El manifiesto de Raphi como módulo de Tiqsi: lo que Qillqa (u otro anfitrión) monta.

Necesita solo la identidad. Avisa a la campana del anfitrión por su bandeja («aviso.nuevo», como Minka y Punku) y,
cuando lleguen sus piezas (R6), aprovechará los objetos de los demás módulos. Ofrece «pdf.v1» y «conversion.v1».
"""
from __future__ import annotations

from tiqsi import EntradaMenu, Manifiesto
from tiqsi.bandeja_sql import BandejaSQL

from raphi import VERSION, db, trabajos
from raphi import config as configuracion
from raphi.api import router
from raphi.contrato import CONVERSION_V1, PDF_V1


async def _preparar(_anfitrion) -> None:
    """Su carpeta, su base (si falta) y sus tablas."""
    cfg = configuracion.config
    for carpeta in (cfg.dir, cfg.subidos, cfg.trabajos):
        carpeta.mkdir(parents=True, exist_ok=True)
    await db.preparar(cfg.database_url)


MANIFIESTO = Manifiesto(
    id="raphi", nombre="Raphi", version=VERSION, contrato="^0.1",
    routers=[router], prefijos=("/api/raphi",),
    necesita=("identidad.v1",),
    aprovecha=("documentos.v1", "recibidos.v1", "rendiciones.v1", "medios.v2", "relaciones.v1"),
    ofrece={"pdf.v1": PDF_V1, "conversion.v1": CONVERSION_V1},
    al_arrancar=[_preparar],
    tareas=[trabajos.repartidor, trabajos.purga],
    bandeja=BandejaSQL(db.fabrica, db.BANDEJA),
    menu=(EntradaMenu("raphi", "Raphi", "/raphi", "PDF, ofimática y conversión de archivos"),),
)
