"""escritorio/studio/servicios/trabajos.py — los trabajos del studio (sin Qt): qué es un trabajo, su archivo para el
corredor, cómo se lee lo que el corredor escribe (el progreso y el informe) y la lista persistida en la caché del
studio (`trabajos.json`, los últimos 200). La cola de la API (`raphi/trabajos.py`) es de la web y de Qillqa; esta es
la de la ventana (`docs/rediseno.md` S3)."""
from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

ESTADOS = (("en_cola", "En cola"), ("en_curso", "En curso"), ("hecho", "Hecho"), ("parcial", "Con errores"), ("fallido", "Fallido"), ("cancelado", "Cancelado"))
TEXTO_DE_ESTADO = dict(ESTADOS)
NIVEL_DE_ESTADO = {"en_cola": "neutro", "en_curso": "activo", "hecho": "positivo", "parcial": "negativo", "fallido": "negativo", "cancelado": "inactivo"}
ICONO_DE_ESTADO = {"en_cola": "chronometer", "en_curso": "media-playback-start", "hecho": "data-success", "parcial": "data-warning", "fallido": "data-error",
                   "cancelado": "process-stop"}
GRUPOS = (("todos", "Todos"), ("en_cola", "En cola"), ("en_curso", "En curso"), ("hechos", "Hechos"), ("con_error", "Con error"))
TOPE = 200
_PROGRESO = re.compile(r"^## progreso (\d+) ?(.*)$")
_INFORME = re.compile(r"^## informe (.*)$")


@dataclass
class Trabajo:
    id: str
    ref: str                              # el id de la operación, o «receta:<id>»
    titulo: str
    archivos: list = field(default_factory=list)
    params: dict = field(default_factory=dict)
    destino: str = ""                     # vacío: junto a cada original
    simular: bool = False
    estado: str = "en_cola"
    progreso: int = 0
    mensaje: str = ""
    informe: dict = field(default_factory=dict)
    salidas: list = field(default_factory=list)
    registro: str = ""
    codigo: int | None = None
    creado: float = 0.0
    inicio: float = 0.0
    fin: float = 0.0

    @property
    def es_receta(self) -> bool:
        return self.ref.startswith("receta:")

    @property
    def grupo(self) -> str:
        if self.estado in ("en_cola", "en_curso"):
            return self.estado
        return "con_error" if self.estado in ("parcial", "fallido") else "hechos"

    @property
    def duracion(self) -> float:
        if not self.inicio:
            return 0.0
        return (self.fin or time.time()) - self.inicio

    def para_corredor(self) -> dict:
        d = {"archivos": list(self.archivos), "params": dict(self.params), "destino": self.destino, "simular": self.simular}
        if self.es_receta:
            d["receta"] = self.ref.split(":", 1)[1]
        else:
            d["operacion"] = self.ref
        return d

    def a_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def de_dict(cls, d: dict) -> "Trabajo":
        campos = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**campos)


def nuevo(ref: str, titulo: str, archivos: list[str], params: dict, destino: str, simular: bool) -> Trabajo:
    return Trabajo(id=uuid.uuid4().hex[:10], ref=ref, titulo=titulo, archivos=list(archivos), params=dict(params), destino=destino or "",
                   simular=simular, creado=time.time())


def progreso_de(linea: str):
    """Para `Tareas.proceso(progreso_de=)`: (porcentaje, mensaje) de una línea `## progreso`, o None."""
    m = _PROGRESO.match(linea.strip())
    return (int(m.group(1)), m.group(2)) if m else None


def informe_de(lineas: list[str]) -> dict | None:
    """El informe que anunció el corredor (`## informe <ruta>`: el JSON está en ese archivo; también vale en línea)."""
    for linea in reversed(lineas):
        m = _INFORME.match(linea.strip())
        if m:
            texto = m.group(1).strip()
            try:
                if texto.startswith("{"):
                    return json.loads(texto)
                return json.loads(Path(texto).read_text(encoding="utf-8"))
            except (ValueError, OSError):
                return None
    return None


def estado_final(codigo: int, informe: dict | None, cancelado: bool) -> tuple[str, str]:
    """(estado, mensaje) al terminar el proceso del corredor."""
    if cancelado:
        return "cancelado", "Cancelado."
    if informe is None:
        return "fallido", f"El corredor terminó con código {codigo} sin informe."
    if informe.get("error"):
        return "fallido", str(informe["error"])
    correctos = informe.get("correctos", sum(1 for e in informe.get("elementos", []) if e.get("ok")))
    fallidos = informe.get("fallidos", sum(1 for e in informe.get("elementos", []) if not e.get("ok")))
    if informe.get("ok", not fallidos):
        return "hecho", (f"{correctos} correcto(s)" if not informe.get("simulado") else f"plan de {correctos} elemento(s)")
    if correctos:
        return "parcial", f"{correctos} correcto(s), {fallidos} con error"
    return "fallido", next((e.get("error") for e in informe.get("elementos", []) if e.get("error")), "Falló.")


def texto_resultado(t: Trabajo) -> str:
    """El Resultado de un trabajo en Markdown: el plan (simulado) o las salidas, y cada error con su archivo."""
    if not t.informe:
        return ""
    partes = []
    if t.informe.get("error"):
        partes.append(f"**No pudo empezar**: {t.informe['error']}")
    for e in t.informe.get("elementos", []):
        nombre = Path(e.get("entrada", "")).name or e.get("entrada", "")
        cabeza = f"### {'·' if t.simular else ('✓' if e.get('ok') else '✗')} {nombre}"
        cuerpo = []
        if e.get("error"):
            cuerpo.append(f"**Error**: {e['error']}")
        for linea in e.get("plan", []):
            cuerpo.append(f"- {linea}")
        for a in e.get("archivos", []):
            cuerpo.append(f"- → `{Path(a).name}` en `{Path(a).parent}`")
        for linea in e.get("mensajes", [])[:12]:
            cuerpo.append(f"- {linea}")
        if e.get("sin_cambio"):
            cuerpo.append("- sin cambio: no hacía falta escribir nada")
        partes.append(cabeza + ("\n\n" + "\n".join(cuerpo) if cuerpo else ""))
    return "\n\n".join(partes) + "\n"


class Lista:
    """La lista de trabajos del studio, persistida."""

    def __init__(self, archivo: Path):
        self.archivo = Path(archivo)
        self.trabajos: list[Trabajo] = []
        try:
            datos = json.loads(self.archivo.read_text(encoding="utf-8"))
            self.trabajos = [Trabajo.de_dict(d) for d in datos.get("trabajos", [])]
        except (OSError, ValueError, TypeError):
            self.trabajos = []
        for t in self.trabajos:                 # lo que quedó a medias al cerrar la ventana no se reanuda solo
            if t.estado in ("en_cola", "en_curso"):
                t.estado, t.mensaje = "cancelado", "La ventana se cerró antes de terminar."

    def guardar(self) -> None:
        try:
            self.archivo.parent.mkdir(parents=True, exist_ok=True)
            self.archivo.write_text(json.dumps({"trabajos": [t.a_dict() for t in self.trabajos[-TOPE:]]}, ensure_ascii=False), encoding="utf-8")
        except (OSError, ValueError):
            pass

    def anadir(self, t: Trabajo) -> None:
        self.trabajos.append(t)
        del self.trabajos[:-TOPE]
        self.guardar()

    def por_id(self, ident: str) -> Trabajo | None:
        return next((t for t in self.trabajos if t.id == ident), None)

    def siguiente_en_cola(self) -> Trabajo | None:
        return next((t for t in self.trabajos if t.estado == "en_cola"), None)

    def contar(self) -> dict:
        c = {"todos": len(self.trabajos), "en_cola": 0, "en_curso": 0, "hechos": 0, "con_error": 0}
        for t in self.trabajos:
            c[t.grupo] += 1
        return c
