"""Recetas: una cadena de operaciones guardada con nombre, que se aplica a un archivo, a un lote o a una carpeta vigilada.

Una receta es un YAML (o JSON) con `nombre`, `descripcion` y `pasos` (cada uno, `operacion` y `params`):

    nombre: Escaneo de mesa de partes
    pasos:
      - operacion: ocr
        params: {idioma: spa}
      - operacion: comprimir
        params: {hasta: 10}

Cada archivo recorre los pasos en una carpeta temporal: lo que sale de un paso es la entrada del siguiente (un paso
que no cambia nada, como comprimir sin ganancia, deja pasar lo que recibió; uno que reparte en varios, como dividir,
sigue con cada parte). El error de un archivo no detiene a los demás. Al final, solo lo último se copia al destino.

Las recetas de serie viven en `raphi/recetas/`; las del usuario, en `$XDG_CONFIG_HOME/raphi/recetas/`.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from raphi.motor import ErrorOperacion, ejecutar, obtener
from raphi.motor.base import Elemento, Informe, Resultado, convertir_parametros

SERIE = Path(__file__).parent / "recetas"


def carpeta_usuario() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "raphi" / "recetas"


@dataclass
class Paso:
    operacion: str
    params: dict = field(default_factory=dict)


@dataclass
class Receta:
    id: str
    nombre: str
    pasos: list[Paso]
    descripcion: str = ""
    sin_entradas: bool = False
    origen: str = "usuario"

    def a_dict(self) -> dict:
        return {"id": self.id, "nombre": self.nombre, "descripcion": self.descripcion, "sin_entradas": self.sin_entradas,
                "origen": self.origen, "pasos": [{"operacion": p.operacion, "params": p.params} for p in self.pasos]}

    def validar(self) -> None:
        if not self.pasos:
            raise ErrorOperacion("La receta no tiene pasos.")
        for i, p in enumerate(self.pasos, 1):
            op = obtener(p.operacion)
            try:
                convertir_parametros(op, p.params)
            except ErrorOperacion as e:
                raise ErrorOperacion(f"Paso {i} ({op.titulo}): {e}") from e


def desde_dict(datos: dict, id: str = "", origen: str = "usuario") -> Receta:
    pasos = [Paso(p["operacion"], dict(p.get("params") or {})) for p in datos.get("pasos") or []]
    r = Receta(id or datos.get("id") or "receta", datos.get("nombre") or id or "Receta", pasos,
               datos.get("descripcion", ""), bool(datos.get("sin_entradas")), origen)
    r.validar()
    return r


def leer(ruta: Path, origen: str = "usuario") -> Receta:
    texto = ruta.read_text(encoding="utf-8")
    if ruta.suffix == ".json":
        datos = json.loads(texto)
    else:
        try:
            import yaml
        except ImportError as e:
            raise ErrorOperacion("Para leer recetas YAML hace falta PyYAML (o guárdela en JSON).") from e
        datos = yaml.safe_load(texto) or {}
    return desde_dict(datos, ruta.stem, origen)


def todas() -> list[Receta]:
    salida, vistas = [], set()
    for carpeta, origen in ((carpeta_usuario(), "usuario"), (SERIE, "serie")):
        if not carpeta.is_dir():
            continue
        for ruta in sorted(carpeta.iterdir()):
            if ruta.suffix in (".yml", ".yaml", ".json") and ruta.stem not in vistas:
                try:
                    salida.append(leer(ruta, origen))
                    vistas.add(ruta.stem)
                except Exception:
                    continue           # una receta rota no esconde a las demás (se ve al abrirla)
    return salida


def buscar(id_o_ruta: str) -> Receta:
    p = Path(id_o_ruta).expanduser()
    if p.is_file():
        return leer(p)
    for r in todas():
        if r.id == id_o_ruta:
            return r
    raise ErrorOperacion(f"No hay una receta «{id_o_ruta}».")


def guardar(receta: Receta) -> Path:
    receta.validar()
    carpeta = carpeta_usuario()
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{receta.id}.json"
    datos = receta.a_dict()
    datos.pop("origen", None)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return ruta


def aplicar(receta: Receta, entradas: list[str | Path], *, destino: str | Path | None = None, simular: bool = False,
            progreso=None, cancelado=None) -> Informe:
    """Aplica la receta. Con varias entradas, cada una por su lado (salvo un paso que no sea de lote, como unir)."""
    rutas = [Path(e).expanduser() for e in entradas]
    if not rutas and not receta.sin_entradas:
        raise ErrorOperacion("Elija al menos un archivo.")
    if simular:
        plan = [f"{i}. {obtener(p.operacion).titulo}" for i, p in enumerate(receta.pasos, 1)]
        primero = ejecutar(receta.pasos[0].operacion, rutas, receta.pasos[0].params, destino=destino, simular=True)
        return Informe(f"receta:{receta.id}", True,
                       [Elemento(e.entrada, e.ok, Resultado(plan=plan + (e.resultado.plan if e.resultado else [])),
                                 error=e.error) for e in primero.elementos])
    grupos = [rutas] if receta.sin_entradas or any(not obtener(p.operacion).lote for p in receta.pasos) else [[r] for r in rutas]
    elementos = []
    for g, grupo in enumerate(grupos):
        inicio = time.monotonic()
        nombre = str(grupo[0]) if len(grupo) == 1 else f"{len(grupo)} archivos"
        trabajo = Path(tempfile.mkdtemp(prefix="raphi-receta-"))
        try:
            actuales = list(grupo)
            for i, paso in enumerate(receta.pasos):
                if progreso:
                    progreso((g + i / len(receta.pasos)) / len(grupos), obtener(paso.operacion).titulo)
                carpeta = trabajo / f"{i + 1:02d}-{paso.operacion}"
                inf = ejecutar(paso.operacion, actuales, paso.params, destino=carpeta, cancelado=cancelado)
                fallo = next((e for e in inf.elementos if not e.ok), None)
                if fallo:
                    raise ErrorOperacion(f"Paso {i + 1} ({obtener(paso.operacion).titulo}): {fallo.error}")
                nuevos = inf.archivos
                if nuevos:
                    actuales = nuevos
                # sin salida (sin cambio, o una operación que solo informa): sigue con lo que tenía
            final = Path(destino).expanduser() if destino else (grupo[0].parent if grupo else Path.cwd())
            final.mkdir(parents=True, exist_ok=True)
            copiados = []
            for a in actuales:
                if any(a == r for r in grupo):
                    continue                    # ningún paso cambió nada: el original no se copia sobre sí mismo
                varias = receta.sin_entradas or not grupo or len(actuales) > 1
                tallo = a.stem if varias else f"{grupo[0].stem}_{receta.id}"
                objetivo = final / f"{tallo}{a.suffix}"
                n = 2
                while objetivo.exists():
                    objetivo = final / f"{tallo}-{n}{a.suffix}"
                    n += 1
                shutil.move(str(a), objetivo)
                copiados.append(objetivo)
            elementos.append(Elemento(nombre, True, Resultado(copiados, mensajes=[f"{len(receta.pasos)} pasos"]),
                                      segundos=time.monotonic() - inicio))
        except ErrorOperacion as e:
            elementos.append(Elemento(nombre, False, error=str(e), segundos=time.monotonic() - inicio))
        finally:
            shutil.rmtree(trabajo, ignore_errors=True)
    return Informe(f"receta:{receta.id}", False, elementos)
