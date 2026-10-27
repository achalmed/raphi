"""El núcleo del motor: cómo se declara una operación y cómo se ejecuta.

Una operación es una función con su ficha (`Operacion`): de qué categoría es, qué recibe, qué parámetros tiene y qué
herramientas del sistema necesita. Se declara con `@operacion(...)` y queda en `REGISTRO`; la CLI, la API y la web
leen esa ficha para armar sus órdenes y formularios, así que una operación existe en un solo lugar.

Tres principios heredados de docflow y pdf-suite (`docs/arquitectura.md` §Principios):

1. **Errores por archivo, nunca por lote**: en una operación de lote cada entrada se procesa aparte; el fallo de una
   se anota y las demás siguen.
2. **El original nunca se toca**: la salida va a otro archivo (sufijo o carpeta de destino) y solo se da por buena si
   se verificó (que exista, que abra y, para un PDF, que tenga páginas).
3. **Simular antes de aplicar**: con `simular=True` la operación dice qué haría y no escribe nada.
"""
from __future__ import annotations

import os
import re
import shutil
import tempfile
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


class ErrorOperacion(Exception):
    """Un fallo explicable de una operación sobre una entrada (se muestra tal cual al usuario)."""


class OperacionDesconocida(LookupError):
    pass


class Cancelado(Exception):
    """El usuario canceló el trabajo."""


# --- parámetros ------------------------------------------------------------------------------------------------

TIPOS = ("texto", "multilinea", "entero", "decimal", "opcion", "casilla", "paginas", "clave", "color", "tamano", "json")


@dataclass(frozen=True)
class Parametro:
    """Un parámetro de una operación. `tipo` decide cómo se pide (formulario) y cómo se convierte (CLI, API)."""

    clave: str
    etiqueta: str
    tipo: str = "texto"
    defecto: Any = None
    opciones: tuple = ()           # para «opcion»: valores (o pares valor, etiqueta)
    minimo: float | None = None
    maximo: float | None = None
    ayuda: str = ""
    obligatorio: bool = False

    def __post_init__(self):
        if self.tipo not in TIPOS:
            raise ValueError(f"Tipo de parámetro desconocido: {self.tipo}")

    def valores(self) -> list[str]:
        return [o[0] if isinstance(o, tuple) else o for o in self.opciones]

    def convertir(self, valor: Any) -> Any:
        """Del texto de la CLI o del JSON de la API al valor que usa la función; error claro si no vale."""
        if valor is None or valor == "":
            if self.obligatorio:
                raise ErrorOperacion(f"Falta «{self.etiqueta}».")
            return self.defecto
        t = self.tipo
        try:
            if t == "entero":
                v = int(valor)
            elif t in ("decimal", "tamano"):
                v = _megas(valor) if t == "tamano" else float(valor)
            elif t == "casilla":
                v = valor if isinstance(valor, bool) else str(valor).strip().lower() in ("1", "si", "sí", "true", "on", "yes")
            elif t == "json":
                import json
                v = valor if not isinstance(valor, str) else json.loads(valor)
            else:
                v = str(valor)
        except (TypeError, ValueError) as e:
            raise ErrorOperacion(f"«{self.etiqueta}» no es válido: {valor!r}.") from e
        if t == "opcion" and self.opciones and v not in self.valores():
            raise ErrorOperacion(f"«{self.etiqueta}» debe ser uno de: {', '.join(self.valores())}.")
        if t in ("entero", "decimal", "tamano"):
            if self.minimo is not None and v < self.minimo:
                raise ErrorOperacion(f"«{self.etiqueta}» no puede ser menor que {self.minimo:g}.")
            if self.maximo is not None and v > self.maximo:
                raise ErrorOperacion(f"«{self.etiqueta}» no puede ser mayor que {self.maximo:g}.")
        return v

    def ficha(self) -> dict:
        d = asdict(self)
        d["opciones"] = [list(o) if isinstance(o, tuple) else [o, o] for o in self.opciones]
        return d


def _megas(valor: Any) -> float:
    """«10», «10MB», «1.5 GB», «800kb» → megabytes."""
    if isinstance(valor, (int, float)):
        return float(valor)
    m = re.fullmatch(r"\s*([\d.,]+)\s*([kmg]?)b?\s*", str(valor).lower())
    if not m:
        raise ValueError(valor)
    n = float(m[1].replace(",", "."))
    return {"k": n / 1024, "": n, "m": n, "g": n * 1024}[m[2]]


# --- la ficha de una operación ---------------------------------------------------------------------------------

ENTRADAS = ("pdf", "pdfs", "documentos", "imagenes", "medios", "archivos", "ninguna")
CATEGORIAS = ("Organizar", "Optimizar", "Convertir", "Editar", "Seguridad", "Información", "Medios", "Archivos")


@dataclass(frozen=True)
class Operacion:
    id: str
    categoria: str
    titulo: str
    descripcion: str
    funcion: Callable[["Contexto"], "Resultado"]
    entrada: str = "pdf"            # qué recibe (ver ENTRADAS)
    lote: bool = True               # True: la función recibe UNA entrada y se llama por cada una (errores por archivo)
    parametros: tuple[Parametro, ...] = ()
    requiere: tuple[str, ...] = ()  # programas del sistema («gs») o módulos de Python («py:pymupdf»)
    extensiones: tuple[str, ...] = (".pdf",)
    minimo_entradas: int = 1
    sufijo: str = ""                # el sufijo de la salida por omisión (sin él, el id)
    palabras: tuple[str, ...] = ()  # para el buscador de la web («juntar», «combinar»…)

    def faltan(self) -> list[str]:
        """Lo que esta máquina no tiene para correrla."""
        return [r for r in self.requiere if not disponible(r)]

    def ficha(self) -> dict:
        return {"id": self.id, "categoria": self.categoria, "titulo": self.titulo, "descripcion": self.descripcion,
                "entrada": self.entrada, "lote": self.lote, "parametros": [p.ficha() for p in self.parametros],
                "requiere": list(self.requiere), "faltan": self.faltan(), "extensiones": list(self.extensiones),
                "minimo_entradas": self.minimo_entradas, "palabras": list(self.palabras)}


REGISTRO: dict[str, Operacion] = {}


def operacion(id: str, categoria: str, titulo: str, descripcion: str, **kw) -> Callable:
    """Decorador: registra la función como operación. Un id repetido es un error de programación."""
    if categoria not in CATEGORIAS:
        raise ValueError(f"Categoría desconocida: {categoria}")

    def registrar(funcion: Callable) -> Callable:
        if id in REGISTRO:
            raise ValueError(f"La operación «{id}» ya está registrada.")
        if kw.get("entrada", "pdf") not in ENTRADAS:
            raise ValueError(f"Entrada desconocida en «{id}»: {kw.get('entrada')}")
        REGISTRO[id] = Operacion(id=id, categoria=categoria, titulo=titulo, descripcion=descripcion, funcion=funcion,
                                 **kw)
        return funcion

    return registrar


def obtener(id: str) -> Operacion:
    try:
        return REGISTRO[id]
    except KeyError:
        raise OperacionDesconocida(f"No hay una operación «{id}».") from None


_CACHE_DISPONIBLE: dict[str, bool] = {}


def disponible(requisito: str) -> bool:
    if requisito not in _CACHE_DISPONIBLE:
        if requisito.startswith("py:"):
            import importlib.util
            _CACHE_DISPONIBLE[requisito] = importlib.util.find_spec(requisito[3:]) is not None
        else:
            _CACHE_DISPONIBLE[requisito] = shutil.which(requisito) is not None
    return _CACHE_DISPONIBLE[requisito]


# --- contexto y resultado --------------------------------------------------------------------------------------


@dataclass
class Resultado:
    """Lo que devuelve una operación sobre una entrada (o sobre el conjunto, si no es de lote)."""

    archivos: list[Path] = field(default_factory=list)
    datos: dict = field(default_factory=dict)
    mensajes: list[str] = field(default_factory=list)
    plan: list[str] = field(default_factory=list)     # lo que haría (al simular)
    sin_cambio: bool = False                           # p. ej. comprimir sin ganancia: no es error, no hay salida

    def a_dict(self) -> dict:
        return {"archivos": [str(a) for a in self.archivos], "datos": self.datos, "mensajes": self.mensajes,
                "plan": self.plan, "sin_cambio": self.sin_cambio}


@dataclass
class Contexto:
    """Lo que una función de operación recibe: sus entradas, sus parámetros ya convertidos y dónde escribir."""

    operacion: Operacion
    entradas: list[Path]
    params: dict
    destino: Path | None = None      # carpeta de salida; None: junto a cada entrada
    simular: bool = False
    sufijo: str = ""
    sobrescribir: bool = False
    progreso: Callable[[float, str], None] | None = None
    cancelado: Callable[[], bool] | None = None
    _temporales: list[Path] = field(default_factory=list)

    @property
    def entrada(self) -> Path:
        return self.entradas[0]

    def p(self, clave: str) -> Any:
        return self.params.get(clave)

    def avisar(self, fraccion: float, mensaje: str = "") -> None:
        if self.cancelado and self.cancelado():
            raise Cancelado("Cancelado.")
        if self.progreso:
            self.progreso(max(0.0, min(1.0, fraccion)), mensaje)

    def salida(self, nombre: str | None = None, extension: str | None = None, base: Path | None = None) -> Path:
        """La ruta de una salida que no pisa nada: `<stem>_<sufijo><ext>` junto a la entrada o en el destino, con «-2»,
        «-3»… si ya existe. `nombre` fija el nombre completo (sin la extensión si se da `extension`)."""
        base = base or self.entrada
        carpeta = self.destino or base.parent
        sufijo = self.sufijo or self.operacion.sufijo or self.operacion.id
        ext = extension if extension is not None else base.suffix
        tallo = nombre if nombre else f"{base.stem}_{sufijo}"
        ruta = carpeta / f"{tallo}{ext}"
        if self.sobrescribir and not any(ruta.resolve() == e.resolve() for e in self.entradas):
            return ruta
        n = 2
        while ruta.exists() or any(ruta.resolve() == e.resolve() for e in self.entradas):
            ruta = carpeta / f"{tallo}-{n}{ext}"
            n += 1
        return ruta

    def carpeta_salida(self, nombre: str | None = None) -> Path:
        ruta = self.salida(nombre=nombre, extension="")
        if not self.simular:
            ruta.mkdir(parents=True)
        return ruta

    def temporal(self, sufijo: str = "") -> Path:
        """Un archivo temporal que se borra al terminar la operación."""
        fd, nombre = tempfile.mkstemp(prefix="raphi-", suffix=sufijo)
        os.close(fd)
        p = Path(nombre)
        self._temporales.append(p)
        return p

    def carpeta_temporal(self) -> Path:
        p = Path(tempfile.mkdtemp(prefix="raphi-"))
        self._temporales.append(p)
        return p

    def limpiar(self) -> None:
        for p in self._temporales:
            shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True)
        self._temporales.clear()


@dataclass
class Elemento:
    """El resultado de una entrada dentro de un informe."""

    entrada: str
    ok: bool
    resultado: Resultado | None = None
    error: str = ""
    segundos: float = 0.0

    def a_dict(self) -> dict:
        return {"entrada": self.entrada, "ok": self.ok, "error": self.error, "segundos": round(self.segundos, 3),
                **(self.resultado.a_dict() if self.resultado else {})}


@dataclass
class Informe:
    operacion: str
    simulado: bool
    elementos: list[Elemento]

    @property
    def ok(self) -> bool:
        return all(e.ok for e in self.elementos)

    @property
    def archivos(self) -> list[Path]:
        return [a for e in self.elementos if e.resultado for a in e.resultado.archivos]

    def a_dict(self) -> dict:
        return {"operacion": self.operacion, "simulado": self.simulado, "ok": self.ok,
                "correctos": sum(e.ok for e in self.elementos), "fallidos": sum(not e.ok for e in self.elementos),
                "elementos": [e.a_dict() for e in self.elementos]}


# --- ejecutar ----------------------------------------------------------------------------------------------------


def convertir_parametros(op: Operacion, crudos: dict | None) -> dict:
    crudos = dict(crudos or {})
    desconocidos = set(crudos) - {p.clave for p in op.parametros}
    if desconocidos:
        raise ErrorOperacion(f"Parámetros desconocidos para «{op.id}»: {', '.join(sorted(desconocidos))}.")
    return {p.clave: p.convertir(crudos.get(p.clave)) for p in op.parametros}


def ejecutar(id: str, entradas: list[str | Path], params: dict | None = None, *, destino: str | Path | None = None,
             simular: bool = False, sufijo: str = "", sobrescribir: bool = False,
             progreso: Callable[[float, str], None] | None = None,
             cancelado: Callable[[], bool] | None = None) -> Informe:
    """Corre una operación. De lote: una vez por entrada, con su error aparte. Si no: una vez con todas."""
    op = obtener(id)
    faltan = op.faltan()
    if faltan:
        raise ErrorOperacion(f"«{op.titulo}» necesita {', '.join(faltan)}, que no está instalado.")
    valores = convertir_parametros(op, params)
    rutas = [Path(e).expanduser() for e in entradas]
    if len(rutas) < op.minimo_entradas:
        raise ErrorOperacion(f"«{op.titulo}» necesita al menos {op.minimo_entradas} archivo(s).")
    if destino is not None:
        destino = Path(destino).expanduser()
        if not simular:
            destino.mkdir(parents=True, exist_ok=True)
    grupos = [[r] for r in rutas] if op.lote else [rutas]
    elementos = []
    for i, grupo in enumerate(grupos):
        ctx = Contexto(op, grupo, valores, destino, simular, sufijo, sobrescribir, cancelado=cancelado,
                       progreso=(lambda f, m, i=i: progreso((i + f) / len(grupos), m)) if progreso else None)
        nombre = str(grupo[0]) if len(grupo) == 1 else f"{len(grupo)} archivos"
        inicio = time.monotonic()
        try:
            for r in grupo:
                if op.entrada != "ninguna" and not r.exists():
                    raise ErrorOperacion(f"No existe: {r}")
                if op.extensiones and r.is_file() and r.suffix.lower() not in op.extensiones:
                    raise ErrorOperacion(f"{r.name}: «{op.titulo}» acepta {', '.join(op.extensiones)}.")
            resultado = op.funcion(ctx)
            if not simular:
                for a in resultado.archivos:
                    verificar_salida(a)
            elementos.append(Elemento(nombre, True, resultado, segundos=time.monotonic() - inicio))
        except Cancelado:
            elementos.append(Elemento(nombre, False, error="Cancelado.", segundos=time.monotonic() - inicio))
            break
        except ErrorOperacion as e:
            elementos.append(Elemento(nombre, False, error=str(e), segundos=time.monotonic() - inicio))
        except Exception as e:  # un fallo inesperado de una entrada no detiene el lote
            elementos.append(Elemento(nombre, False, error=f"{type(e).__name__}: {e}", segundos=time.monotonic() - inicio))
        finally:
            ctx.limpiar()
    return Informe(op.id, simular, elementos)


def verificar_salida(ruta: Path) -> None:
    """Toda salida existe y no está vacía; un PDF, además, abre y tiene páginas."""
    if ruta.is_dir():
        if not any(ruta.iterdir()):
            raise ErrorOperacion(f"La carpeta de salida quedó vacía: {ruta.name}")
        return
    if not ruta.is_file() or ruta.stat().st_size == 0:
        raise ErrorOperacion(f"La salida no se escribió: {ruta.name}")
    if ruta.suffix.lower() == ".pdf":
        import pikepdf
        try:
            with pikepdf.open(ruta) as pdf:
                if not len(pdf.pages):
                    raise ErrorOperacion(f"La salida quedó sin páginas: {ruta.name}")
        except pikepdf.PasswordError:
            pass                       # cifrado a propósito: abre con su contraseña (lo comprueba «cifrar»)
        except pikepdf.PdfError as e:
            raise ErrorOperacion(f"La salida no es un PDF válido: {ruta.name}") from e


def paginas_de(ruta: Path, clave: str = "") -> int:
    """Páginas de un PDF (0 si no abre)."""
    import pikepdf
    try:
        with pikepdf.open(ruta, password=clave) as pdf:
            return len(pdf.pages)
    except Exception:
        return 0
