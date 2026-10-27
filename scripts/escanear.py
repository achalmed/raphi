#!/usr/bin/env python3
"""scripts/escanear.py — la guarda del repositorio público: nada privado sale hacia GitHub.

Raphi es público con toda su historia (propuesta-raphi §3.4 y §9.2, en el repo de Qillqa). En lugar de una rama
huérfana de demo, cada envío pasa por el escáner común de Tiqsi (`tiqsi.demo.escanear`): términos privados (los
patrones de meta/doctor y los datos del despacho que usa la plataforma, leídos en cada corrida y nunca impresos),
correos de dominios reales, IP públicas, celulares, tokens y binarios fuera de su sitio. Un hallazgo y no sale nada.

Uso (desde la raíz del repo):
    python3 scripts/escanear.py                  # escanea HEAD
    python3 scripts/escanear.py --ref <commit>   # un commit
    python3 scripts/escanear.py --trabajo        # la copia de trabajo (antes de un commit)
    python3 scripts/escanear.py --instalar-guarda  # .git/hooks/pre-push: escanea cada commit que se envía
Salida: 0 limpio · 1 hallazgos · 2 error de entorno (sin Tiqsi no se envía nada).
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
import warnings
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _espacio():
    """La raíz del espacio de trabajo (la que tiene core/env.py) y, por ella, DESPACHO_DIR y META_DIR."""
    up = RAIZ
    while up != up.parent and not (up / "core" / "env.py").exists():
        up = up.parent
    if not (up / "core" / "env.py").exists():
        d, m = os.environ.get("DESPACHO_DIR"), os.environ.get("META_DIR")
        return None, (Path(d) if d else None), (Path(m) if m else None)
    sys.path.insert(0, str(up / "core"))
    import env  # noqa: E402
    return up, Path(env.DESPACHO_DIR), Path(env.META_DIR)


ESPACIO, DESPACHO_DIR, META_DIR = _espacio()
if ESPACIO and (ESPACIO / "tiqsi" / "tiqsi").is_dir():
    sys.path.insert(0, str(ESPACIO / "tiqsi"))
try:
    from tiqsi import demo as comun  # noqa: E402
except ImportError:
    print("[error] Falta Tiqsi (tiqsi.demo): sin el escáner no se envía nada.", file=sys.stderr)
    sys.exit(2)

OPERACIONES = (next((DESPACHO_DIR / "operaciones" / n for n in ("qillqa", "sgdp") if (DESPACHO_DIR / "operaciones" / n).is_dir()),
                    DESPACHO_DIR / "operaciones" / "qillqa") if DESPACHO_DIR else None)
PRIVADO = Path(os.environ.get("DEMO_PRIVADO") or (OPERACIONES / "demo" if OPERACIONES else ""))


def terminos_privados() -> tuple[list[str], list[re.Pattern]]:
    """Los mismos de las demos de la plataforma: patrones sensibles del espacio de trabajo y datos del despacho."""
    fijos: set[str] = set()
    regex: list[re.Pattern] = []
    if META_DIR:
        warnings.filterwarnings("ignore", category=FutureWarning)   # los patrones de meta/doctor son de otro repo
        for n in ("patrones_sensibles.txt", "patrones_credenciales.txt"):
            regex += [re.compile(l, re.I) for l in comun.lineas(META_DIR / "doctor" / n)]
    if DESPACHO_DIR:
        yml = DESPACHO_DIR / "despacho.yml"
        if yml.exists():
            for l in yml.read_text().splitlines():
                m = re.match(r"^\s*(nombre|titular|siglas|bancada|correo|telefono|celular|ruc|dni)\s*:\s*(.+)$", l)
                if m and len(m[2].strip(" '\"")) >= 4:
                    fijos.add(m[2].strip(" '\""))
        env = OPERACIONES / ".env" if OPERACIONES else None
        if env and env.exists():
            for l in env.read_text().splitlines():
                m = re.match(r"^\s*([A-Z_][A-Z0-9_]*)=(.*)$", l)
                if m and any(k in m[1] for k in ("CLAVE", "SECRET", "TOKEN", "PASSWORD", "SIGLAS", "NOMBRE")):
                    v = m[2].split(" #", 1)[0].strip().strip("'\"")
                    if len(v) >= 4:
                        fijos.add(v)
    return sorted(fijos, key=len, reverse=True), regex


def receta() -> "comun.Receta":
    return comun.Receta(raiz=RAIZ, demo=RAIZ / "demo", privado=PRIVADO if str(PRIVADO) else None,
                        terminos=terminos_privados, cache="raphi-guarda", guion="scripts/escanear.py")


GUARDA = """#!/bin/sh
# Guarda pre-push de Raphi (generada por scripts/escanear.py --instalar-guarda; no se edita a mano).
# El repositorio es público: cada commit que sale pasa por el escáner de Tiqsi. Un hallazgo y no sale nada.
cero=0000000000000000000000000000000000000000
while read ref_local sha_local ref_remota sha_remota; do
    [ "$sha_local" = "$cero" ] && continue
    python3 "$(git rev-parse --show-toplevel)/scripts/escanear.py" --ref "$sha_local" --breve || {
        echo "[guarda] $ref_local no sale: el escáner encontró algo (python3 scripts/escanear.py --ref $sha_local)." >&2
        exit 1
    }
done
exit 0
"""


def instalar_guarda() -> int:
    gancho = RAIZ / ".git" / "hooks" / "pre-push"
    if gancho.exists() and "scripts/escanear.py" not in gancho.read_text():
        print(f"[error] Ya hay un pre-push propio en {gancho}: súmale la guarda a mano.", file=sys.stderr)
        return 2
    gancho.write_text(GUARDA)
    gancho.chmod(0o755)
    print(f"[ok] Guarda instalada en {gancho}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="La guarda del repositorio público de Raphi.")
    ap.add_argument("--ref", default="HEAD", help="commit que se escanea (por defecto HEAD)")
    ap.add_argument("--trabajo", action="store_true", help="escanea la copia de trabajo en vez de un commit")
    ap.add_argument("--instalar-guarda", action="store_true", help="instala el pre-push que escanea cada envío")
    ap.add_argument("--breve", action="store_true", help="solo el resultado (lo usa la guarda)")
    a = ap.parse_args(argv)
    if a.instalar_guarda:
        return instalar_guarda()
    r = receta()
    with tempfile.TemporaryDirectory(prefix="raphi-escaneo-") as tmp:
        arbol = Path(tmp)
        comun.extraer(RAIZ, arbol, a.trabajo, a.ref)
        hallazgos = comun.escanear(r, arbol)
    if hallazgos:
        print(f"[FALLA] {len(hallazgos)} hallazgos en {'la copia de trabajo' if a.trabajo else a.ref}:")
        for h in hallazgos[:200]:
            print("  " + h)
        return 1
    if not a.breve:
        print("[ok] Escáner limpio: ningún término privado, correo real, IP pública, celular, token ni binario fuera de sitio.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
