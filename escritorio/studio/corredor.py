#!/usr/bin/env python3
"""escritorio/studio/corredor.py — el motor de Raphi como proceso, para Raphi Studio (`docs/rediseno.md` S1 y S2).

Corre con el `.venv` del repo (el intérprete que tiene pikepdf, PyMuPDF, Pillow, pyhanko…), mientras la ventana corre
con el Python del sistema. Sin Qt y sin importar nada del studio: solo `raphi`.

    corredor.py fichas                 # JSON: las fichas de las operaciones, las recetas, la versión y el intérprete
    corredor.py doctor                 # qué falta en esta máquina (texto, como `raphi doctor`)
    corredor.py ejecutar trabajo.json  # corre un trabajo: {operacion | receta, archivos, params, destino, simular}

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
    print("corredor.py: fichas · doctor · ejecutar <trabajo.json>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
