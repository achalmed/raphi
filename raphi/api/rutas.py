"""Las rutas de `/api/raphi`: operaciones, archivos, trabajos y recetas.

Toda ruta pide la identidad del anfitrión (`tiqsi.puertos.usuario_actual`): una cuenta solo ve sus archivos y sus
trabajos. En el modo escritorio hay además `POST /locales`, que registra archivos del disco sin copiarlos, y un
trabajo puede escribir «junto» al original o en una carpeta elegida; fuera del escritorio eso se rechaza.
"""
from __future__ import annotations

import io
import mimetypes
import shutil
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select

from raphi import config as configuracion
from raphi import db, recetas, trabajos
from raphi.motor import ErrorOperacion, OperacionDesconocida
from raphi.motor.documentos import estado_docflow, limpiar_cache_docflow
from tiqsi.puertos import Usuario, solo_administrador, usuario_actual

router = APIRouter(prefix="/api/raphi", tags=["raphi"])


def _cfg():
    return configuracion.config


# --- operaciones ---------------------------------------------------------------------------------------------------


@router.get("/operaciones")
async def operaciones(_u: Usuario = Depends(usuario_actual)) -> dict:
    from raphi import motor
    from raphi.fuentes import disponibles
    return {"operaciones": motor.operaciones(), "categorias": motor.categorias(), "fuentes": disponibles(),
            "modo": _cfg().modo, "recetas": [r.a_dict() for r in recetas.todas()]}


@router.get("/sistema")
async def sistema(_u: Usuario = Depends(usuario_actual)) -> dict:
    """El diagnóstico (lo que la GUI tenía en Sistema → Diagnóstico): qué hay instalado y qué operaciones faltan."""
    from raphi import VERSION, motor
    from raphi.motor.base import disponible
    requeridos = sorted({r for op in motor.REGISTRO.values() for r in op.requiere})
    cfg = _cfg()
    return {"version": VERSION, "modo": cfg.modo, "concurrencia": cfg.concurrencia,
            "retencion_horas": cfg.retencion_horas, "tope_subida_mb": cfg.tope_subida_mb,
            "requisitos": [{"nombre": r.removeprefix("py:"), "python": r.startswith("py:"), "ok": disponible(r),
                            "usan": [op.id for op in motor.REGISTRO.values() if r in op.requiere]} for r in requeridos],
            "no_disponibles": [op.id for op in motor.REGISTRO.values() if op.faltan()],
            "carpeta": str(cfg.dir) if cfg.escritorio else None,
            "docflow": estado_docflow()}


class LimpiarCache(BaseModel):
    vaciar: bool = False


@router.post("/sistema/docflow/cache")
async def cache_docflow(cuerpo: LimpiarCache, _u: Usuario = Depends(solo_administrador)) -> dict:
    """Compacta la caché de docflow (o la vacía, con `vaciar`): lo que antes se hacía con `docflow cache` en la terminal."""
    import asyncio
    try:
        mensaje = await asyncio.to_thread(limpiar_cache_docflow, cuerpo.vaciar)
    except ErrorOperacion as e:
        raise HTTPException(409, str(e)) from e
    return {"mensaje": mensaje, "docflow": estado_docflow()}


@router.get("/formatos")
async def formatos(nombre: str = Query(..., description="el nombre del archivo: lo que importa es su extensión"),
                   _u: Usuario = Depends(usuario_actual)) -> list[dict]:
    from raphi.motor.medios import formatos_de
    return formatos_de(Path(nombre).name)


# --- archivos ------------------------------------------------------------------------------------------------------


def _ficha_archivo(fila) -> dict:
    ruta = Path(fila.ruta)
    ficha = {"id": fila.id, "nombre": fila.nombre, "bytes": fila.bytes, "local": fila.local,
             "tipo": mimetypes.guess_type(fila.nombre)[0] or "application/octet-stream"}
    if ruta.suffix.lower() == ".pdf":
        from raphi.motor.base import paginas_de
        ficha["paginas"] = paginas_de(ruta) or None
    if fila.local:
        ficha["ruta"] = str(ruta)
    return ficha


async def _archivo(ident: str, u: Usuario):
    async with db.sesion() as s:
        fila = (await s.execute(select(db.ARCHIVOS).where(db.ARCHIVOS.c.id == ident,
                                                          db.ARCHIVOS.c.cuenta == u.id))).first()
    if fila is None:
        raise HTTPException(404, "Ese archivo no existe o ya se borró.")
    return fila


@router.post("/archivos")
async def subir(archivos: list[UploadFile] = File(...), u: Usuario = Depends(usuario_actual)) -> list[dict]:
    from tiqsi.nombres import sanear
    tope = _cfg().tope_subida_mb * 1024 * 1024
    fichas = []
    for a in archivos:
        ident = trabajos.nuevo_id()
        nombre = Path(a.filename or "archivo").name
        tallo, ext = Path(nombre).stem, Path(nombre).suffix.lower()
        carpeta = _cfg().subidos / ident
        carpeta.mkdir(parents=True, exist_ok=True)
        destino = carpeta / f"{sanear(tallo) or 'archivo'}{ext}"
        escritos = 0
        with destino.open("wb") as f:
            while trozo := await a.read(1024 * 1024):
                escritos += len(trozo)
                if escritos > tope:
                    f.close()
                    shutil.rmtree(carpeta, ignore_errors=True)
                    raise HTTPException(413, f"{nombre} pasa de {_cfg().tope_subida_mb} MB.")
                f.write(trozo)
        async with db.sesion() as s:
            await s.execute(db.ARCHIVOS.insert().values(id=ident, cuenta=u.id, nombre=nombre, ruta=str(destino),
                                                        bytes=escritos, local=False))
            await s.commit()
        fichas.append(_ficha_archivo(await _archivo(ident, u)))
    return fichas


class Locales(BaseModel):
    rutas: list[str] = Field(..., min_length=1)


@router.post("/locales")
async def locales(cuerpo: Locales, u: Usuario = Depends(usuario_actual)) -> list[dict]:
    """Solo el escritorio: archivos del disco de esta máquina, por su ruta (no se copian ni se borran nunca)."""
    if not _cfg().escritorio:
        raise HTTPException(403, "Solo Raphi escritorio trabaja con archivos del disco.")
    fichas = []
    for r in cuerpo.rutas:
        ruta = Path(r).expanduser()
        if not ruta.exists():
            raise HTTPException(404, f"No existe: {ruta}")
        ident = trabajos.nuevo_id()
        async with db.sesion() as s:
            await s.execute(db.ARCHIVOS.insert().values(id=ident, cuenta=u.id, nombre=ruta.name, ruta=str(ruta),
                                                        bytes=ruta.stat().st_size if ruta.is_file() else 0, local=True))
            await s.commit()
        fichas.append(_ficha_archivo(await _archivo(ident, u)))
    return fichas


@router.get("/archivos/{ident}")
async def ficha(ident: str, u: Usuario = Depends(usuario_actual)) -> dict:
    return _ficha_archivo(await _archivo(ident, u))


@router.get("/archivos/{ident}/info")
async def info(ident: str, u: Usuario = Depends(usuario_actual)) -> dict:
    fila = await _archivo(ident, u)
    from raphi.motor.pdf_info import informacion
    if not fila.nombre.lower().endswith(".pdf"):
        raise HTTPException(400, "La información detallada es de los PDF.")
    return informacion(Path(fila.ruta))


@router.get("/archivos/{ident}/contenido")
async def contenido(ident: str, peticion: Request, u: Usuario = Depends(usuario_actual)) -> Response:
    from tiqsi.web import enviar_archivo
    fila = await _archivo(ident, u)
    ruta = Path(fila.ruta)
    if not ruta.is_file():
        raise HTTPException(404, "El archivo ya no está en el disco.")
    return enviar_archivo(ruta, fila.nombre, mimetypes.guess_type(fila.nombre)[0] or "application/octet-stream", peticion)


@router.get("/archivos/{ident}/miniatura")
async def miniatura(ident: str, pagina: int = Query(1, ge=1), ancho: int = Query(220, ge=32, le=1600),
                    u: Usuario = Depends(usuario_actual)) -> Response:
    """Una página como imagen WebP (la mesa de trabajo y el visor). Se guarda junto al archivo: la segunda vez es
    instantánea."""
    import asyncio
    fila = await _archivo(ident, u)
    ruta = Path(fila.ruta)
    cache = (_cfg().dir / "miniaturas" / ident) if fila.local else ruta.parent / ".miniaturas"
    destino = cache / f"p{pagina}-w{ancho}.webp"
    if not destino.is_file():
        def hacer():
            import pymupdf
            from PIL import Image
            with pymupdf.open(ruta) as doc:
                if pagina > doc.page_count:
                    raise HTTPException(404, f"El documento tiene {doc.page_count} páginas.")
                p = doc[pagina - 1]
                zoom = ancho / p.rect.width
                img = p.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
            cache.mkdir(parents=True, exist_ok=True)
            Image.frombytes("RGB", (img.width, img.height), img.samples).save(destino, "WEBP", quality=78)
        if ruta.suffix.lower() != ".pdf":
            raise HTTPException(400, "Las miniaturas son de los PDF.")
        await asyncio.to_thread(hacer)
    return Response(destino.read_bytes(), media_type="image/webp", headers={"Cache-Control": "private, max-age=86400"})


@router.delete("/archivos/{ident}")
async def borrar(ident: str, u: Usuario = Depends(usuario_actual)) -> dict:
    fila = await _archivo(ident, u)
    if not fila.local:
        shutil.rmtree(Path(fila.ruta).parent, ignore_errors=True)
    async with db.sesion() as s:
        await s.execute(db.ARCHIVOS.delete().where(db.ARCHIVOS.c.id == ident))
        await s.commit()
    return {"borrado": ident}


# --- trabajos ------------------------------------------------------------------------------------------------------


class Pedido(BaseModel):
    operacion: str = Field(..., description="el id de una operación o «receta:<id>»")
    archivos: list[str] = Field(default_factory=list)
    params: dict = Field(default_factory=dict)
    simular: bool = False
    destino: str = Field("", description="escritorio: «junto» al original o una carpeta")


@router.post("/trabajos")
async def crear_trabajo(pedido: Pedido, u: Usuario = Depends(usuario_actual)) -> dict:
    if pedido.destino and not _cfg().escritorio:
        raise HTTPException(403, "Elegir dónde se escribe es solo de Raphi escritorio.")
    for a in pedido.archivos:
        await _archivo(a, u)
    try:
        return await trabajos.encolar(u.id, pedido.operacion, pedido.archivos, pedido.params, simular=pedido.simular,
                                      destino=pedido.destino)
    except OperacionDesconocida as e:
        raise HTTPException(404, str(e)) from e
    except ErrorOperacion as e:
        raise HTTPException(422, str(e)) from e


@router.get("/trabajos")
async def listar_trabajos(u: Usuario = Depends(usuario_actual)) -> list[dict]:
    return await trabajos.listar(u.id)


@router.get("/trabajos/{ident}")
async def trabajo(ident: str, u: Usuario = Depends(usuario_actual)) -> dict:
    t = await trabajos.obtener_trabajo(ident, u.id)
    if t is None:
        raise HTTPException(404, "Ese trabajo no existe o ya se borró.")
    return t


@router.post("/trabajos/{ident}/cancelar")
async def cancelar(ident: str, u: Usuario = Depends(usuario_actual)) -> dict:
    return {"cancelado": await trabajos.cancelar(ident, u.id)}


async def _salidas(ident: str, u: Usuario) -> list[Path]:
    async with db.sesion() as s:
        fila = (await s.execute(select(db.TRABAJOS.c.salidas).where(db.TRABAJOS.c.id == ident,
                                                                    db.TRABAJOS.c.cuenta == u.id))).first()
    if fila is None:
        raise HTTPException(404, "Ese trabajo no existe o ya se borró.")
    return [Path(r) for r in fila.salidas or []]


def _zip(rutas: list[Path]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for r in rutas:
            for p in ([r] if r.is_file() else sorted(x for x in r.rglob("*") if x.is_file())):
                z.write(p, p.name if r.is_file() else Path(r.name) / p.relative_to(r))
    return buf.getvalue()


@router.get("/trabajos/{ident}/salidas/{n}")
async def descargar(ident: str, n: int, peticion: Request, u: Usuario = Depends(usuario_actual)) -> Response:
    from tiqsi.web import enviar_archivo
    salidas = await _salidas(ident, u)
    if not 0 <= n < len(salidas) or not salidas[n].exists():
        raise HTTPException(404, "Esa salida no existe o ya se borró.")
    r = salidas[n]
    if r.is_dir():
        return Response(_zip([r]), media_type="application/zip",
                        headers={"Content-Disposition": f'attachment; filename="{r.name}.zip"'})
    return enviar_archivo(r, r.name, mimetypes.guess_type(r.name)[0] or "application/octet-stream", peticion)


@router.get("/trabajos/{ident}/zip")
async def descargar_todo(ident: str, u: Usuario = Depends(usuario_actual)) -> StreamingResponse:
    salidas = [r for r in await _salidas(ident, u) if r.exists()]
    if not salidas:
        raise HTTPException(404, "El trabajo no dejó salidas.")
    return StreamingResponse(io.BytesIO(_zip(salidas)), media_type="application/zip",
                             headers={"Content-Disposition": f'attachment; filename="raphi-{ident[:8]}.zip"'})


@router.post("/trabajos/{ident}/salidas/{n}/a-archivo")
async def salida_como_archivo(ident: str, n: int, u: Usuario = Depends(usuario_actual)) -> dict:
    """Una salida vuelve a ser entrada (encadenar a mano: comprimir y luego foliar, sin descargar ni subir)."""
    salidas = await _salidas(ident, u)
    if not 0 <= n < len(salidas) or not salidas[n].is_file():
        raise HTTPException(404, "Esa salida no existe o es una carpeta.")
    r = salidas[n]
    nuevo = trabajos.nuevo_id()
    carpeta = _cfg().subidos / nuevo
    carpeta.mkdir(parents=True)
    copia = carpeta / r.name
    shutil.copy2(r, copia)
    async with db.sesion() as s:
        await s.execute(db.ARCHIVOS.insert().values(id=nuevo, cuenta=u.id, nombre=r.name, ruta=str(copia),
                                                    bytes=copia.stat().st_size, local=False))
        await s.commit()
    return _ficha_archivo(await _archivo(nuevo, u))


# --- recetas -------------------------------------------------------------------------------------------------------


@router.get("/recetas")
async def listar_recetas(_u: Usuario = Depends(usuario_actual)) -> list[dict]:
    return [r.a_dict() for r in recetas.todas()]


class RecetaNueva(BaseModel):
    id: str = Field(..., pattern=r"^[a-z0-9][a-z0-9-]{1,60}$")
    nombre: str
    descripcion: str = ""
    pasos: list[dict]


@router.post("/recetas")
async def guardar_receta(cuerpo: RecetaNueva, _u: Usuario = Depends(usuario_actual)) -> dict:
    try:
        r = recetas.desde_dict(cuerpo.model_dump(), cuerpo.id)
        recetas.guardar(r)
    except (ErrorOperacion, OperacionDesconocida) as e:
        raise HTTPException(422, str(e)) from e
    return r.a_dict()


@router.delete("/recetas/{ident}")
async def borrar_receta(ident: str, _u: Usuario = Depends(usuario_actual)) -> dict:
    for ext in (".json", ".yml", ".yaml"):
        p = recetas.carpeta_usuario() / f"{ident}{ext}"
        if p.is_file():
            p.unlink()
            return {"borrada": ident}
    raise HTTPException(404, "Solo se borran las recetas propias (las de serie no).")
