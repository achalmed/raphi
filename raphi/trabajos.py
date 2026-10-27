"""La cola de trabajos: lo largo (OCR de 300 páginas, un lote de compresión) corre aparte y se mira mientras avanza.

Un trabajo se guarda en la base como «pendiente»; el repartidor (una tarea del anfitrión) toma los pendientes de a
`RAPHI_CONCURRENCIA` y corre el motor en un hilo (el trabajo pesado es de Ghostscript, OCRmyPDF, qpdf o ffmpeg, en
procesos aparte). El avance vive en memoria y se guarda en la base cada segundo; cancelar es pedirlo y el motor lo
mira entre página y página. Al arrancar, lo que quedó «en_curso» (la API se reinició) vuelve a «pendiente»: sus
salidas van a una carpeta nueva, así que repetirlo no pisa nada. Al terminar se anota «raphi.trabajo.terminado» en su
bandeja de salida, en la misma transacción, y, si tardó más de `AVISAR_DESDE` segundos, «aviso.nuevo» (la campana
del anfitrión, como hacen Minka y Punku: datos `usuario_id`, `texto`, `tipo`, `destino`).

La purga borra a las `RAPHI_RETENCION_HORAS` los archivos subidos y las salidas (nunca los archivos locales del
escritorio, que no son suyos).
"""
from __future__ import annotations

import asyncio
import datetime as dt
import logging
import shutil
import time
import uuid
from pathlib import Path

from sqlalchemy import delete, select, update

from raphi import config as configuracion
from raphi import db

registro = logging.getLogger("raphi.trabajos")

AVISAR_DESDE = 30          # segundos: lo rápido no llena la campana
PROGRESO: dict[str, tuple[float, str]] = {}
CANCELAR: set[str] = set()
_despertar: asyncio.Event | None = None


def nuevo_id() -> str:
    return uuid.uuid4().hex


def _ahora() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def avisar_nuevo() -> None:
    if _despertar is not None:
        _despertar.set()


async def encolar(cuenta: int, operacion: str, archivos: list[str], params: dict, *, simular: bool = False,
                  destino: str = "", referencia: str = "") -> dict:
    """Valida lo que se pueda validar antes de encolar (que la operación exista y sus parámetros valgan)."""
    from raphi.motor import obtener
    from raphi.motor.base import convertir_parametros
    if operacion.startswith("receta:"):
        from raphi import recetas
        receta = recetas.buscar(operacion.split(":", 1)[1])
        titulo = receta.nombre
    else:
        op = obtener(operacion)
        convertir_parametros(op, params)
        titulo = op.titulo
    ident = nuevo_id()
    fila = dict(id=ident, cuenta=cuenta, operacion=operacion, titulo=titulo, params=params, archivos=archivos,
                destino=destino, simular=simular, estado="pendiente", progreso=0.0, mensaje="", salidas=[],
                referencia=referencia, creado_en=_ahora())        # con microsegundos: el orden de la lista
    async with db.sesion() as s:
        await s.execute(db.TRABAJOS.insert().values(**fila))
        await s.commit()
    avisar_nuevo()
    return await obtener_trabajo(ident)


async def obtener_trabajo(ident: str, cuenta: int | None = None) -> dict | None:
    async with db.sesion() as s:
        q = select(db.TRABAJOS).where(db.TRABAJOS.c.id == ident)
        if cuenta is not None:
            q = q.where(db.TRABAJOS.c.cuenta == cuenta)
        fila = (await s.execute(q)).mappings().first()
    if fila is None:
        return None
    t = dict(fila)
    if ident in PROGRESO and t["estado"] == "en_curso":
        t["progreso"], t["mensaje"] = PROGRESO[ident]
    for k in ("creado_en", "terminado_en"):
        t[k] = t[k].isoformat() if t[k] else None
    t["salidas"] = [{"n": i, "nombre": Path(r).name, "bytes": Path(r).stat().st_size if Path(r).is_file() else None,
                     "carpeta": Path(r).is_dir(), "ruta": r if configuracion.config.escritorio else None}
                    for i, r in enumerate(t["salidas"] or [])]
    return t


async def listar(cuenta: int, limite: int = 50) -> list[dict]:
    async with db.sesion() as s:
        ids = (await s.execute(select(db.TRABAJOS.c.id).where(db.TRABAJOS.c.cuenta == cuenta)
                               .order_by(db.TRABAJOS.c.creado_en.desc()).limit(limite))).scalars().all()
    return [t for i in ids if (t := await obtener_trabajo(i))]


async def cancelar(ident: str, cuenta: int) -> bool:
    t = await obtener_trabajo(ident, cuenta)
    if t is None or t["estado"] not in ("pendiente", "en_curso"):
        return False
    CANCELAR.add(ident)
    if t["estado"] == "pendiente":
        async with db.sesion() as s:
            await s.execute(update(db.TRABAJOS).where(db.TRABAJOS.c.id == ident, db.TRABAJOS.c.estado == "pendiente")
                            .values(estado="cancelado", terminado_en=_ahora(), mensaje="Cancelado."))
            await s.commit()
    return True


async def rutas_de(archivos: list[str]) -> list[Path]:
    if not archivos:
        return []
    async with db.sesion() as s:
        filas = {f.id: f for f in (await s.execute(select(db.ARCHIVOS).where(db.ARCHIVOS.c.id.in_(archivos)))).all()}
    faltan = [a for a in archivos if a not in filas]
    if faltan:
        raise LookupError(f"Archivos que ya no están (¿purgados?): {', '.join(faltan)}")
    return [Path(filas[a].ruta) for a in archivos]


def _correr(t: dict, entradas: list[Path], carpeta: Path) -> tuple[dict, list[str]]:
    """El trabajo en sí (en un hilo): el motor o una receta, con avance y cancelación."""
    from raphi import motor, recetas
    ident = t["id"]

    def progreso(fraccion: float, mensaje: str) -> None:
        PROGRESO[ident] = (fraccion, mensaje)

    def cancelado() -> bool:
        return ident in CANCELAR

    if t["destino"] == "junto":
        destino = None
    elif t["destino"]:
        destino = Path(t["destino"]).expanduser()
    else:
        destino = carpeta
    if t["operacion"].startswith("receta:"):
        receta = recetas.buscar(t["operacion"].split(":", 1)[1])
        informe = recetas.aplicar(receta, entradas, destino=destino or carpeta, simular=t["simular"], progreso=progreso,
                                  cancelado=cancelado)
    else:
        informe = motor.ejecutar(t["operacion"], entradas, t["params"], destino=destino, simular=t["simular"],
                                 progreso=progreso, cancelado=cancelado)
    return informe.a_dict(), [str(a) for a in informe.archivos]


async def _ejecutar(t: dict) -> None:
    ident = t["id"]
    carpeta = configuracion.config.trabajos / ident
    inicio = time.monotonic()
    PROGRESO[ident] = (0.0, "")
    async with db.sesion() as s:
        await s.execute(update(db.TRABAJOS).where(db.TRABAJOS.c.id == ident).values(estado="en_curso", progreso=0.0))
        await s.commit()

    async def guardar_avance():
        while True:
            await asyncio.sleep(1)
            f, m = PROGRESO.get(ident, (0.0, ""))
            async with db.sesion() as s:
                await s.execute(update(db.TRABAJOS).where(db.TRABAJOS.c.id == ident).values(progreso=f, mensaje=m[:500]))
                await s.commit()

    vigilante = asyncio.create_task(guardar_avance())
    try:
        entradas = await rutas_de(t["archivos"])
        if not t["simular"]:
            carpeta.mkdir(parents=True, exist_ok=True)
        informe, salidas = await asyncio.to_thread(_correr, t, entradas, carpeta)
        if ident in CANCELAR:
            estado, mensaje = "cancelado", "Cancelado."
        elif informe["ok"]:
            estado, mensaje = "hecho", f"{informe['correctos']} correcto(s)"
        elif informe["correctos"]:
            estado, mensaje = "parcial", f"{informe['correctos']} correcto(s), {informe['fallidos']} con error"
        else:
            estado = "fallido"
            mensaje = next((e["error"] for e in informe["elementos"] if e["error"]), "Falló.")
    except Exception as e:  # el trabajo falla, la cola sigue
        registro.exception("El trabajo %s falló.", ident)
        informe, salidas, estado, mensaje = None, [], "fallido", f"{type(e).__name__}: {e}"
    finally:
        vigilante.cancel()
        PROGRESO.pop(ident, None)
        CANCELAR.discard(ident)
    from tiqsi.bandeja_sql import guardar
    async with db.sesion() as s:
        await s.execute(update(db.TRABAJOS).where(db.TRABAJOS.c.id == ident).values(
            estado=estado, progreso=1.0, mensaje=mensaje[:1000], informe=informe, salidas=salidas, terminado_en=_ahora()))
        await guardar(s, db.BANDEJA, "raphi.trabajo.terminado",
                      {"trabajo": ident, "cuenta": t["cuenta"], "estado": estado, "titulo": t["titulo"],
                       "referencia": t["referencia"]}, origen="raphi")
        if time.monotonic() - inicio >= AVISAR_DESDE:
            palabra = {"hecho": "listo", "parcial": "terminado con errores", "fallido": "falló", "cancelado": "cancelado"}
            await guardar(s, db.BANDEJA, "aviso.nuevo", {"usuario_id": t["cuenta"], "tipo": "raphi.trabajo",
                                                          "texto": f"Raphi · {t['titulo']}: {palabra[estado]}",
                                                          "destino": f"raphi:{ident}"}, origen="raphi")
        await s.commit()


async def reanudar() -> int:
    """Lo que quedó a medias al apagarse vuelve a la cola."""
    async with db.sesion() as s:
        r = await s.execute(update(db.TRABAJOS).where(db.TRABAJOS.c.estado == "en_curso")
                            .values(estado="pendiente", progreso=0.0, mensaje="Reanudado tras un reinicio."))
        await s.commit()
    return r.rowcount or 0


async def repartidor(_anfitrion=None, intervalo: float = 2.0) -> None:
    """La tarea en segundo plano del módulo: corre los pendientes, de a `RAPHI_CONCURRENCIA`."""
    global _despertar
    _despertar = asyncio.Event()
    cupo = asyncio.Semaphore(configuracion.config.concurrencia)
    en_marcha: set[asyncio.Task] = set()
    tomados: set[str] = set()
    await reanudar()
    while True:
        async with db.sesion() as s:
            pendientes = (await s.execute(select(db.TRABAJOS).where(db.TRABAJOS.c.estado == "pendiente")
                                          .order_by(db.TRABAJOS.c.creado_en).limit(20))).mappings().all()
        for t in pendientes:
            if t["id"] in tomados or cupo.locked():
                continue
            tomados.add(t["id"])

            async def uno(t=dict(t)):
                async with cupo:
                    try:
                        await _ejecutar(t)
                    finally:
                        tomados.discard(t["id"])

            tarea = asyncio.create_task(uno())
            en_marcha.add(tarea)
            tarea.add_done_callback(en_marcha.discard)
        try:
            await asyncio.wait_for(_despertar.wait(), timeout=intervalo)
        except asyncio.TimeoutError:
            pass
        _despertar.clear()


async def purgar(ahora: dt.datetime | None = None) -> int:
    """Borra lo vencido: archivos subidos (no los locales) y trabajos terminados con sus salidas."""
    limite = (ahora or _ahora()) - dt.timedelta(hours=configuracion.config.retencion_horas)
    borrados = 0
    async with db.sesion() as s:
        viejos = (await s.execute(select(db.ARCHIVOS).where(db.ARCHIVOS.c.creado_en < limite,
                                                            db.ARCHIVOS.c.local.is_(False)))).all()
        for a in viejos:
            shutil.rmtree(Path(a.ruta).parent, ignore_errors=True)
            borrados += 1
        await s.execute(delete(db.ARCHIVOS).where(db.ARCHIVOS.c.id.in_([a.id for a in viejos])))
        terminados = (await s.execute(select(db.TRABAJOS.c.id, db.TRABAJOS.c.destino).where(
            db.TRABAJOS.c.terminado_en < limite))).all()
        for t in terminados:
            if not t.destino:                     # las salidas propias; lo que se escribió en una carpeta elegida, no
                shutil.rmtree(configuracion.config.trabajos / t.id, ignore_errors=True)
        await s.execute(delete(db.TRABAJOS).where(db.TRABAJOS.c.id.in_([t.id for t in terminados])))
        await s.commit()
    return borrados + len(terminados)


async def purga(_anfitrion=None, cada: float = 3600) -> None:
    while True:
        try:
            await purgar()
        except Exception:  # noqa: BLE001
            registro.exception("La purga falló; se reintenta en la próxima vuelta.")
        await asyncio.sleep(cada)


async def esperar(ident: str, tope: float = 120) -> dict:
    """Para las pruebas y la capacidad síncrona: espera a que un trabajo termine."""
    inicio = time.monotonic()
    while time.monotonic() - inicio < tope:
        t = await obtener_trabajo(ident)
        if t and t["estado"] not in ("pendiente", "en_curso"):
            return t
        await asyncio.sleep(0.1)
    raise TimeoutError(ident)
