"""escritorio/studio/servicios/fichas.py — las fichas de las herramientas (las operaciones del motor y las recetas),
tal como las devuelve el corredor (`corredor.py fichas`, en el intérprete del motor: `faltan` se calcula donde se va a
correr), guardadas en la caché del studio para abrir al instante y releídas en segundo plano. Sin Qt.

Una receta se vuelve una ficha más (`es_receta`), sin parámetros, con la entrada y las extensiones de su primer paso;
la ventana la simula y la aplica como una herramienta (`docs/rediseno.md` S6)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from escritorio.studio import familias
from escritorio.studio.servicios import rutas

LARGOS = ("whisper", "yt-dlp", "ocrmypdf")            # programas que tardan: aplicar avisa y el trabajo muestra su progreso


def leer_cache(archivo: Path) -> dict | None:
    try:
        return json.loads(Path(archivo).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def guardar_cache(archivo: Path, datos: dict) -> None:
    try:
        Path(archivo).parent.mkdir(parents=True, exist_ok=True)
        Path(archivo).write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def pedir(interprete: str | None = None, plazo: int = 120) -> dict:
    """Las fichas desde el corredor (un proceso del intérprete del motor). Lanza si el corredor falla."""
    r = subprocess.run([interprete or rutas.interprete_motor(), str(rutas.CORREDOR), "fichas"], capture_output=True, text=True, timeout=plazo,
                       cwd=str(rutas.REPO))
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip().splitlines()[-1] if r.stderr.strip() else f"el corredor salió con {r.returncode}")
    return json.loads(r.stdout)


def herramientas(datos: dict) -> list[dict]:
    """Las fichas de la ventana: cada operación con su familia e icono, y cada receta como herramienta de Recetas."""
    salida = []
    for f in datos.get("operaciones", []):
        salida.append(dict(f, es_receta=False, familia=familias.familia_de(f), icono=familias.icono_de(f), ref=f["id"],
                           larga=any(r in LARGOS for r in f.get("requiere", []))))
    for r in datos.get("recetas", []):
        salida.append({"id": r["id"], "ref": f"receta:{r['id']}", "titulo": r["nombre"], "descripcion": r.get("descripcion") or "Receta: " + " → ".join(p["titulo"] for p in r["pasos"]),
                       "categoria": "Recetas", "entrada": r["entrada"], "lote": True, "parametros": [], "requiere": [], "faltan": r.get("faltan", []),
                       "extensiones": r.get("extensiones", []), "minimo_entradas": r.get("minimo_entradas", 1), "palabras": [p["titulo"] for p in r["pasos"]],
                       "es_receta": True, "familia": "recetas", "icono": "view-list-tree", "pasos": r["pasos"], "origen": r.get("origen", ""),
                       "larga": False})
    return salida


def acepta_texto(f: dict) -> str:
    """Qué acepta la herramienta, para la tabla: las extensiones, o «carpetas», «cualquier archivo» o «ninguno»."""
    if f.get("entrada") == "ninguna" or f.get("minimo_entradas", 1) == 0:
        return "ninguno (trabaja sin archivos)"
    ext = f.get("extensiones") or []
    if not ext:
        return "carpetas" if familias.trabaja_con_carpetas(f) else "cualquier archivo"
    return " ".join(e.lstrip(".").upper() for e in ext[:6]) + (" …" if len(ext) > 6 else "")


def entrada_texto(f: dict) -> str:
    if f.get("entrada") == "ninguna":
        return "sin archivos"
    n = f.get("minimo_entradas", 1)
    base = f"{n} o más" if n > 1 else "uno o más"
    return base + (" (cada uno por su lado)" if f.get("lote") else " (todos juntos)")


def resumen_markdown(f: dict) -> str:
    """El Resumen de una herramienta en Markdown: qué hace, qué recibe, qué produce, qué necesita y sus opciones."""
    partes = [f"# {f['titulo']}", f.get("descripcion", "")]
    datos = [f"**Familia**: {familias.nombre_de(f.get('familia', ''))}", f"**Categoría**: {f.get('categoria', '')}",
             f"**Recibe**: {entrada_texto(f)} · {acepta_texto(f)}"]
    if f.get("es_receta"):
        datos.append("**Pasos**: " + " → ".join(p["titulo"] for p in f.get("pasos", [])))
        datos.append(f"**Origen**: {f.get('origen') or 'de serie'}")
    if f.get("requiere"):
        datos.append("**Necesita**: " + ", ".join(r.removeprefix("py:") + (" (Python)" if r.startswith("py:") else "") for r in f["requiere"]))
    if f.get("faltan"):
        datos.append("**Falta en esta máquina**: " + ", ".join(x.removeprefix("py:") for x in f["faltan"]))
    if f.get("larga"):
        datos.append("**Tarda**: el trabajo muestra su progreso y se cancela con Esc")
    partes.append("  \n".join(datos))
    if f.get("parametros"):
        partes.append("## Opciones\n\n" + "\n".join(f"- **{p['etiqueta']}** (`{p['clave']}`, {p['tipo']}" + (f", por omisión `{p['defecto']}`" if p.get("defecto") not in (None, "") else "") + ")"
                                                     + (f": {p['ayuda']}" if p.get("ayuda") else "") for p in f["parametros"]))
    elif f.get("es_receta"):
        partes.append("Una receta no tiene opciones: cada paso lleva las suyas guardadas.")
    else:
        partes.append("Esta herramienta no tiene opciones.")
    if f.get("palabras"):
        partes.append("*También*: " + ", ".join(f["palabras"]))
    return "\n\n".join(p for p in partes if p) + "\n"


def campos_formulario(f: dict) -> list[dict]:
    """Los campos de `PaginaFormulario` desde los parámetros de la ficha: los tipos del motor que el marco no tiene se
    traducen (paginas y tamano a texto con su marcador; json a multilínea)."""
    salida = []
    for p in f.get("parametros", []):
        tipo = p["tipo"]
        marcador = ""
        if tipo == "paginas":
            tipo, marcador = "texto", "todas · 1-3,5 · último"
        elif tipo == "tamano":
            tipo, marcador = "texto", "p. ej. 10 MB"
        elif tipo == "json":
            tipo, marcador = "multilinea", "JSON"
        salida.append({"clave": p["clave"], "etiqueta": p["etiqueta"], "tipo": tipo, "defecto": p.get("defecto"), "opciones": p.get("opciones") or [],
                       "minimo": p.get("minimo"), "maximo": p.get("maximo"), "ayuda": p.get("ayuda") or "", "obligatorio": bool(p.get("obligatorio")),
                       "marcador": marcador})
    return salida
