"""La CLI de Raphi: cada operación del motor es una orden, con sus parámetros como opciones.

    python -m raphi lista                                  # las operaciones, por categoría
    python -m raphi ayuda comprimir                        # sus parámetros
    python -m raphi comprimir a.pdf b.pdf --hasta 10 -n    # simular (-n) y luego aplicar
    python -m raphi formatos foto.heic                     # a qué se puede convertir (el menú de Tangerine)
    python -m raphi recetas                                # las recetas guardadas
    python -m raphi receta escaneo-mesa-de-partes *.pdf -o salida/
    python -m raphi doctor                                 # qué falta en esta máquina
    python -m raphi accion comprimir a.pdf --hasta 10      # lo de los menús de Dolphin: junto al original y aviso al final

Salida: 0 todo bien · 1 algún archivo falló · 2 error de uso · 130 cancelado. Con --json, el informe en JSON.
"""
from __future__ import annotations

import argparse
import json
import sys

from raphi import VERSION, motor
from raphi.motor.base import ErrorOperacion, OperacionDesconocida, obtener


def _imprimir_informe(informe, como_json: bool) -> int:
    if como_json:
        print(json.dumps(informe.a_dict(), ensure_ascii=False, indent=2))
        return 0 if informe.ok else 1
    for e in informe.elementos:
        marca = "·" if informe.simulado else ("✓" if e.ok else "✗")
        print(f"{marca} {e.entrada}")
        if e.error:
            print(f"    {e.error}")
        if e.resultado:
            for linea in e.resultado.plan + e.resultado.mensajes:
                print(f"    {linea}")
            for a in e.resultado.archivos:
                print(f"    → {a}")
    if not informe.simulado and len(informe.elementos) > 1:
        bien = sum(e.ok for e in informe.elementos)
        print(f"{bien} de {len(informe.elementos)} correctos")
    return 0 if informe.ok else 1


def _opciones_de(op, ap: argparse.ArgumentParser) -> None:
    for p in op.parametros:
        nombre = "--" + p.clave.replace("_", "-")
        ayuda = p.etiqueta + (f" ({p.ayuda})" if p.ayuda else "")
        if p.tipo == "opcion":
            ayuda += f" [{' | '.join(p.valores())}]"
        if p.defecto not in (None, ""):
            ayuda += f" · por omisión: {p.defecto}"
        if p.tipo == "casilla":
            ap.add_argument(nombre, dest=p.clave, action=argparse.BooleanOptionalAction, default=None, help=ayuda)
        else:
            ap.add_argument(nombre, dest=p.clave, default=None, help=ayuda, metavar=p.tipo.upper())


def _lista() -> int:
    for categoria in motor.categorias():
        print(f"\n{categoria}")
        for f in motor.operaciones():
            if f["categoria"] == categoria:
                falta = f"  (falta {', '.join(f['faltan'])})" if f["faltan"] else ""
                print(f"  {f['id']:<26} {f['titulo']}{falta}")
    return 0


def _doctor() -> int:
    from raphi.motor.base import disponible
    requeridos = sorted({r for op in motor.REGISTRO.values() for r in op.requiere})
    faltan = [r for r in requeridos if not disponible(r)]
    for r in requeridos:
        print(f"  {'✓' if disponible(r) else '✗'} {r.removeprefix('py:')}{' (Python)' if r.startswith('py:') else ''}")
    sin = [op.id for op in motor.REGISTRO.values() if op.faltan()]
    print(f"\n{len(motor.REGISTRO) - len(sin)} de {len(motor.REGISTRO)} operaciones disponibles"
          + (f"; sin: {', '.join(sin)}" if sin else ""))
    return 1 if faltan else 0


def _avisar_escritorio(titulo: str, informe) -> None:
    """El aviso del sistema al terminar una acción del menú de Dolphin (notify-send, si está)."""
    import shutil
    import subprocess
    if not shutil.which("notify-send"):
        return
    bien = sum(e.ok for e in informe.elementos)
    salidas = [a.name for a in informe.archivos]
    texto = (f"{bien} de {len(informe.elementos)} listos" + (f": {', '.join(salidas[:3])}" if salidas else "")
             + ("" if informe.ok else f" · {next(e.error for e in informe.elementos if not e.ok)}"))
    subprocess.run(["notify-send", "-a", "Raphi", "-i", "document-edit", f"Raphi · {titulo}", texto], check=False)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    if argv[0] in ("-V", "--version"):
        print(f"raphi {VERSION}")
        return 0
    orden, resto = argv[0], argv[1:]
    try:
        if orden == "lista":
            return _lista()
        if orden == "doctor":
            return _doctor()
        if orden == "ayuda":
            op = obtener(resto[0]) if resto else None
            if not op:
                return _lista()
            ap = argparse.ArgumentParser(prog=f"raphi {op.id}", description=f"{op.titulo}: {op.descripcion}")
            _opciones_de(op, ap)
            ap.print_help()
            return 0
        if orden == "formatos":
            from raphi.motor.medios import formatos_de
            for ruta in resto:
                print(ruta)
                for f in formatos_de(ruta):
                    print(f"  {('→ ' + f['a']) if f['a'] else '  ' :<10} {f['titulo']:<34} raphi {f['operacion']}"
                          + "".join(f" --{k} {v}" for k, v in f["params"].items()))
            return 0
        if orden == "recetas":
            from raphi import recetas
            for r in recetas.todas():
                print(f"  {r.id:<28} {r.nombre} ({r.origen}) — {' → '.join(p.operacion for p in r.pasos)}")
            return 0
        if orden == "receta":
            from raphi import recetas
            ap = argparse.ArgumentParser(prog="raphi receta")
            ap.add_argument("receta")
            ap.add_argument("entradas", nargs="*")
            ap.add_argument("-o", "--destino")
            ap.add_argument("-n", "--simular", action="store_true")
            ap.add_argument("--json", action="store_true")
            a = ap.parse_args(resto)
            informe = recetas.aplicar(recetas.buscar(a.receta), a.entradas, destino=a.destino, simular=a.simular)
            return _imprimir_informe(informe, a.json)

        accion = orden == "accion"
        if accion:
            if not resto:
                print("raphi accion <operación> [opciones] archivos…", file=sys.stderr)
                return 2
            orden, resto = resto[0], resto[1:]
        op = obtener(orden)
        ap = argparse.ArgumentParser(prog=f"raphi {op.id}", description=f"{op.titulo}: {op.descripcion}")
        ap.add_argument("entradas", nargs="*" if op.minimo_entradas == 0 else "+", help="archivos")
        ap.add_argument("-o", "--destino", help="carpeta de salida (por omisión, junto a cada archivo)")
        ap.add_argument("-n", "--simular", action="store_true", help="dice qué haría, sin escribir nada")
        ap.add_argument("-s", "--sufijo", default="", help=f"sufijo de la salida (por omisión «_{op.sufijo or op.id}»)")
        ap.add_argument("--json", action="store_true", help="el informe en JSON")
        _opciones_de(op, ap)
        a = ap.parse_args(resto)
        params = {p.clave: getattr(a, p.clave) for p in op.parametros if getattr(a, p.clave) is not None}

        def progreso(fraccion, mensaje):
            if sys.stderr.isatty() and not a.json:
                print(f"\r  {fraccion * 100:5.1f} % {mensaje[:50]:<50}", end="", file=sys.stderr, flush=True)

        informe = motor.ejecutar(op.id, a.entradas, params, destino=a.destino, simular=a.simular, sufijo=a.sufijo,
                                 progreso=progreso)
        if sys.stderr.isatty() and not a.json:
            print("\r" + " " * 62 + "\r", end="", file=sys.stderr)
        if accion:
            _avisar_escritorio(op.titulo, informe)
        return _imprimir_informe(informe, a.json)
    except OperacionDesconocida as e:
        print(f"raphi: {e} (raphi lista)", file=sys.stderr)
        return 2
    except ErrorOperacion as e:
        print(f"raphi: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nraphi: cancelado.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
