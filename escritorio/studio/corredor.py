#!/usr/bin/env python3
"""escritorio/studio/corredor.py — el motor de Raphi como proceso, para Raphi Studio (`docs/rediseno.md` S1 y S2).

Corre con el `.venv` del repo (el intérprete que tiene pikepdf, PyMuPDF, Pillow, pyhanko…), mientras la ventana corre
con el Python del sistema. Sin Qt y sin importar nada del studio: solo `raphi`.

    corredor.py fichas                 # JSON: las fichas de las operaciones, las recetas, la versión y el intérprete
    corredor.py doctor                 # qué falta en esta máquina (texto, como `raphi doctor`)
    corredor.py ejecutar trabajo.json  # corre un trabajo: {operacion | receta, archivos, params, destino, simular}
    corredor.py rueda archivo…         # JSON: lo que la rueda de soltar ofrece para esos archivos (o enlaces) juntos, con sus fichas
    corredor.py vista trabajo.json     # una vista previa: la operación de verdad en una carpeta temporal, y su archivo
    corredor.py actuales op archivo    # JSON: los valores que el archivo ya tiene en esa operación (rellenar el formulario)

`ejecutar` escribe cada archivo con su resultado o su error (para el panel inferior), el avance en líneas
`## progreso <0-100> <mensaje>` (la barra de estado) y, al final, el informe del motor en JSON junto al archivo del
trabajo (`<trabajo>.informe.json`), anunciado con `## informe <ruta>`. Sale 0 si todo fue bien, 1 si algún archivo falló, 2 si el trabajo no pudo empezar. Cancelar es matar el
proceso (gui_comun.tareas mata al grupo entero: también el gs, ffmpeg o whisper que esté corriendo).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


def fichas() -> dict:
    from raphi import VERSION, motor, recetas
    lista = []
    for r in recetas.todas():
        try:
            primero = motor.obtener(r.pasos[0].operacion)
        except Exception:       # noqa: BLE001  una receta con un paso desconocido no tumba la lista
            continue
        lista.append({"id": r.id, "nombre": r.nombre, "descripcion": r.descripcion, "origen": r.origen, "sin_entradas": r.sin_entradas,
                      "pasos": [{"operacion": p.operacion, "titulo": motor.obtener(p.operacion).titulo if p.operacion in motor.REGISTRO else p.operacion,
                                 "params": dict(p.params)} for p in r.pasos],
                      "entrada": "ninguna" if r.sin_entradas else primero.entrada, "extensiones": list(primero.extensiones),
                      "minimo_entradas": 0 if r.sin_entradas else 1,
                      "faltan": sorted({x for p in r.pasos if p.operacion in motor.REGISTRO for x in motor.obtener(p.operacion).faltan()})})
    return {"version": VERSION, "interprete": sys.executable, "categorias": motor.categorias(), "operaciones": motor.operaciones(),
            "recetas": lista}


def rueda(rutas: list[str]) -> dict:
    """Las opciones de la rueda (`motor.medios.opciones_para`) con lo que la ventana necesita de cada ficha."""
    from raphi import VERSION, motor
    from raphi.motor.audio_video import opciones_para_enlaces
    from raphi.motor.medios import opciones_para
    from escritorio.studio.familias import icono_de          # el mapa de iconos de Raphi (Python puro, sin Qt)
    fichas = {f["id"]: f for f in motor.operaciones()}
    opciones = []
    enlaces = [r for r in rutas if r.startswith(("http://", "https://"))]
    for o in (opciones_para_enlaces(enlaces) if enlaces else opciones_para(rutas)):
        f = fichas[o["operacion"]]
        opciones.append({**o, "descripcion": f["descripcion"], "categoria": f["categoria"], "lote": f["lote"],
                         "parametros": f["parametros"], "faltan": f["faltan"], "con_actuales": f.get("con_actuales", False),
                         **({} if o.get("icono") else {"icono": icono_de(f)})})
    return {"version": VERSION, "opciones": opciones}


VISIBLES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg"}
IMAGENES = VISIBLES | {".heic", ".heif", ".avif", ".tif", ".tiff"}


TEXTOS = {".txt", ".md", ".srt", ".vtt", ".csv", ".tsv", ".json", ".html", ".htm"}
TOPE_TEXTO = 400_000


def vista(ruta_trabajo: str) -> int:
    """Corre la operación de verdad sobre una copia (las imágenes grandes, reducidas a `reducir` px de lado mayor) en
    la carpeta `destino` del trabajo, que es temporal y de la ventana, y anuncia en una línea
    `## vista {"archivo": ruta, "tipo": imagen|pdf|texto|"", "tamano": bytes, "nombre": salida}` el archivo que la
    ventana muestra: la salida misma (un PDF entero, para el visor con zoom y búsqueda), la imagen pasada a PNG si Qt no
    la lee, o el texto. Nunca escribe junto al original; la copia y lo demás se borran al terminar."""
    import shutil
    import tempfile
    t = json.loads(Path(ruta_trabajo).read_text(encoding="utf-8"))
    destino = Path(t["destino"])
    destino.mkdir(parents=True, exist_ok=True)
    trabajo = Path(tempfile.mkdtemp(prefix="raphi-vista-", dir=destino))
    try:
        return _vista(t, trabajo, destino / f"vista-{Path(ruta_trabajo).stem}")
    finally:
        shutil.rmtree(trabajo, ignore_errors=True)


def _vista(t: dict, trabajo: Path, base: Path) -> int:
    import shutil
    from raphi import motor
    from raphi.motor.base import ErrorOperacion
    entrada = Path(t["archivos"][0])
    copia = trabajo / entrada.name
    reducir = int(t.get("reducir") or 0)
    ext = entrada.suffix.lower()
    if reducir and ext in IMAGENES and ext != ".svg":
        from raphi.motor.medios import _abrir_imagen
        img = _abrir_imagen(entrada)
        if max(img.size) > reducir:
            img.thumbnail((reducir, reducir))
        if ext in (".jpg", ".jpeg"):                 # el mismo formato: la vista de «comprimir» muestra su pérdida
            img.convert("RGB").save(copia, "JPEG", quality=95)
        elif ext in (".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"):
            img.save(copia)
        else:                                        # HEIC, AVIF: a PNG (Pillow quizá no los escriba)
            copia = copia.with_suffix(".png")
            img.save(copia, "PNG")
    else:
        shutil.copy2(entrada, copia)
    try:
        informe = motor.ejecutar(t["operacion"], [copia], t.get("params") or {}, destino=trabajo, sobrescribir=True)
    except ErrorOperacion as error:
        print(f"raphi: {error}", flush=True)
        return 1
    e = informe.elementos[0] if informe.elementos else None
    if e is None or not e.ok:
        print(f"raphi: {e.error if e else 'sin resultado'}", flush=True)
        return 1
    salidas = [a for a in informe.archivos if a.is_file()] or [x for a in informe.archivos if a.is_dir() for x in sorted(a.rglob("*")) if x.is_file()]
    if not salidas:
        print("## vista " + json.dumps({"archivo": "", "tipo": "", "tamano": 0, "nombre": ""}), flush=True)
        return 0
    salida = salidas[0]
    ext = salida.suffix.lower()
    tipo = ""
    if ext in VISIBLES and ext != ".svg":
        tipo, archivo = "imagen", base.with_suffix(ext)
        shutil.copy2(salida, archivo)
    elif ext in IMAGENES:
        from raphi.motor.medios import _abrir_imagen
        tipo, archivo = "imagen", base.with_suffix(".png")
        _abrir_imagen(salida).save(archivo, "PNG")
    elif ext == ".pdf":
        tipo, archivo = "pdf", base.with_suffix(".pdf")
        shutil.copy2(salida, archivo)
    elif ext in TEXTOS:
        tipo, archivo = "texto", base.with_suffix(".txt")
        archivo.write_text(salida.read_text(encoding="utf-8", errors="replace")[:TOPE_TEXTO], encoding="utf-8")
    else:
        archivo = None
    print("## vista " + json.dumps({"archivo": str(archivo or ""), "tipo": tipo, "tamano": salida.stat().st_size,
                                    "nombre": salida.name}, ensure_ascii=False), flush=True)
    return 0


def actuales(operacion: str, ruta: str) -> dict:
    """Lo que el archivo ya tiene en los parámetros de la operación (`motor.base.actuales`)."""
    from raphi.motor.base import actuales as leer
    return leer(operacion, ruta)


def doctor() -> int:
    from raphi.__main__ import main
    return main(["doctor"])


def ejecutar(ruta_trabajo: str) -> int:
    from raphi import motor, recetas
    from raphi.motor.base import ErrorOperacion
    t = json.loads(Path(ruta_trabajo).read_text(encoding="utf-8"))
    entradas = list(t.get("archivos") or [])
    destino = t.get("destino") or None
    simular = bool(t.get("simular"))

    def progreso(fraccion: float, mensaje: str = "") -> None:
        print(f"## progreso {int(max(0.0, min(1.0, fraccion)) * 100)} {mensaje}", flush=True)

    try:
        if t.get("receta"):
            receta = recetas.buscar(t["receta"])
            informe = recetas.aplicar(receta, entradas, destino=destino, simular=simular, progreso=progreso)
        else:
            informe = motor.ejecutar(t["operacion"], entradas, t.get("params") or {}, destino=destino, simular=simular, progreso=progreso)
    except ErrorOperacion as e:
        print(f"raphi: {e}", flush=True)
        _informe(ruta_trabajo, {"ok": False, "error": str(e), "elementos": [], "simulado": simular})
        return 2
    for e in informe.elementos:
        marca = "·" if informe.simulado else ("✓" if e.ok else "✗")
        print(f"{marca} {e.entrada}", flush=True)
        if e.error:
            print(f"    {e.error}", flush=True)
        if e.resultado:
            for linea in e.resultado.plan + e.resultado.mensajes:
                print(f"    {linea}", flush=True)
            for a in e.resultado.archivos:
                print(f"    → {a}", flush=True)
    if not informe.simulado and len(informe.elementos) > 1:
        print(f"{sum(x.ok for x in informe.elementos)} de {len(informe.elementos)} correctos", flush=True)
    _informe(ruta_trabajo, informe.a_dict())
    return 0 if informe.ok else 1


def _informe(ruta_trabajo: str, datos: dict) -> None:
    ruta = Path(ruta_trabajo).with_suffix(".informe.json")
    ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    print(f"## informe {ruta}", flush=True)


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    if argv[0] == "fichas":
        print(json.dumps(fichas(), ensure_ascii=False))
        return 0
    if argv[0] == "doctor":
        return doctor()
    if argv[0] == "ejecutar" and len(argv) > 1:
        return ejecutar(argv[1])
    if argv[0] == "rueda":
        print(json.dumps(rueda(argv[1:]), ensure_ascii=False))
        return 0
    if argv[0] == "vista" and len(argv) > 1:
        return vista(argv[1])
    if argv[0] == "actuales" and len(argv) > 2:
        print(json.dumps(actuales(argv[1], argv[2]), ensure_ascii=False))
        return 0
    print("corredor.py: fichas · doctor · ejecutar <trabajo.json> · rueda <archivos…> · vista <trabajo.json> · actuales <op> <archivo>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
