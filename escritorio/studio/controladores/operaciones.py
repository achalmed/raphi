"""escritorio/studio/controladores/operaciones.py — la operación actual (del catálogo `servicios.operaciones`):
Simular (F5: la herramienta sobre los archivos con las opciones como trabajo simulado; o la CLI de solo lectura del
motor, en el panel inferior) y Aplicar (Ctrl+Intro, tras confirmar en QML con la herramienta, los archivos, las
opciones y el destino); por qué no se puede; el texto de la confirmación. Los menús de Dolphin y las carpetas
vigiladas también viven aquí (escriben en la configuración del escritorio)."""
from __future__ import annotations

import time
from pathlib import Path

from gui_comun.qt import QObject, QSettings, Property, Signal, Slot

from escritorio.studio.servicios import operaciones as ops
from escritorio.studio.servicios import rutas


class Operaciones(QObject):
    cambiado = Signal()
    corridaCambiada = Signal()
    terminada = Signal(str, bool, int)      # id de la operación de la CLI, aplicar, código
    aviso = Signal(str, str)

    def __init__(self, espacio, herramientas, archivos, trabajos, consola, tareas, cache: Path | None = None, parent=None):
        super().__init__(parent)
        self.espacio, self.herramientas, self.archivos, self.trabajos, self.consola, self.tareas = espacio, herramientas, archivos, trabajos, consola, tareas
        self._s = QSettings()
        self._cache = (cache or herramientas._cache) / "operaciones"
        guardada = str(self._s.value("operacion/actual", "herramienta") or "herramienta")
        self._actual = guardada if ops.operacion(guardada) else "herramienta"
        self._worker = None
        self._lineas: list[str] = []
        self._inicio = 0.0
        herramientas.actualCambiado.connect(self.cambiado)
        herramientas.opcionesCambiadas.connect(self.cambiado)
        archivos.cambiado.connect(self.cambiado)
        trabajos.cambiado.connect(self.cambiado)
        tareas.cambiada.connect(self.cambiado)
        tareas.linea.connect(self._linea)
        self._vigilancia = None

    # ------------------------------------------------------------ la operación actual
    def _op(self) -> ops.Operacion | None:
        return ops.operacion(self._actual)

    @Property("QVariantList", constant=True)
    def lista(self) -> list:
        return [{"id": o.id, "titulo": o.titulo, "descripcion": o.descripcion, "icono": o.icono} for o in ops.OPERACIONES]

    @Property(int, notify=cambiado)
    def indiceActual(self) -> int:
        return next((i for i, o in enumerate(ops.OPERACIONES) if o.id == self._actual), -1)

    @Slot(int)
    def fijarPorIndice(self, i: int) -> None:
        if 0 <= i < len(ops.OPERACIONES):
            self.fijar(ops.OPERACIONES[i].id)

    @Slot(str)
    def fijar(self, id_: str) -> None:
        if ops.operacion(id_) is None:
            return
        if id_ != self._actual:
            self._actual = id_
            self._s.setValue("operacion/actual", id_)
        self.cambiado.emit()
        self.corridaCambiada.emit()

    @Property(str, notify=cambiado)
    def actual(self) -> str:
        return self._actual

    @Property(str, notify=cambiado)
    def titulo(self) -> str:
        o = self._op()
        return o.titulo if o else ""

    @Property(str, notify=cambiado)
    def descripcion(self) -> str:
        o = self._op()
        return o.descripcion if o else ""

    @Property(str, notify=cambiado)
    def verbo(self) -> str:
        o = self._op()
        return o.verbo if o else "Simular"

    @Property(bool, notify=cambiado)
    def escribe(self) -> bool:
        o = self._op()
        return bool(o and o.escribe)

    @Property(bool, notify=cambiado)
    def esTrabajo(self) -> bool:
        o = self._op()
        return bool(o and o.trabajo)

    @Property(str, notify=cambiado)
    def queToca(self) -> str:
        o = self._op()
        return o.toca if o else ""

    @Property(str, notify=cambiado)
    def ordenSimular(self) -> str:
        o = self._op()
        if o is None:
            return ""
        if o.trabajo:
            h = self.herramientas
            return f"{'receta' if h.esReceta else 'operación'} {h.id} · {self.archivos.total} archivo(s) · {h.textoOpciones} · salida: {h.destinoEfectivo} · simulada (corredor del motor, -n)"
        try:
            return o.cli(list(self.archivos.rutas)).texto()
        except Exception as e:      # noqa: BLE001
            return f"(no se puede armar la orden: {e})"

    @Property(str, notify=cambiado)
    def ordenAplicar(self) -> str:
        o = self._op()
        if o is None or not o.trabajo:
            return ""
        h = self.herramientas
        return f"{'receta' if h.esReceta else 'operación'} {h.id} · {self.archivos.total} archivo(s) · {h.textoOpciones} · salida: {h.destinoEfectivo} · de verdad (corredor del motor)"

    # ----------------------------------------------------------- disponibilidad
    @Property(bool, notify=cambiado)
    def enCurso(self) -> bool:
        return (self._worker is not None and self._worker.isRunning()) or self.trabajos.enCurso

    @Property(str, notify=cambiado)
    def motivoNoSimular(self) -> str:
        o = self._op()
        h = self.herramientas
        if o is None:
            return "No hay operación elegida."
        if self._worker is not None and self._worker.isRunning():
            return "Hay una orden de la CLI en curso (Esc la cancela)."
        if o.sobre_archivos and self.archivos.total == 0:
            return "Añade archivos a la lista (pestaña Archivos, o suéltalos sobre la ventana)."
        if not o.trabajo:
            return ""
        if not h.hayActual:
            return "Elige primero una herramienta en el catálogo."
        if h.faltan:
            return "Falta en esta máquina: " + ", ".join(h.faltan) + "."
        if not h.sinArchivos and self.archivos.total < h.minimoEntradas:
            return f"«{h.titulo}» necesita al menos {h.minimoEntradas} archivo(s): añádelos (pestaña Archivos) o suéltalos sobre la ventana."
        if not h.sinArchivos and not h.aceptaLosArchivos:
            return f"«{h.titulo}» acepta {h.textoAcepta}: quita de la lista lo que no sirva."
        if h.enCarpeta and not h.destino.strip():
            return "Elige la carpeta de salida (pestaña Opciones) o deja la salida junto a cada original."
        return ""

    @Property(bool, notify=cambiado)
    def puedeSimular(self) -> bool:
        return self.motivoNoSimular == ""

    @Property(str, notify=cambiado)
    def motivoNoAplicar(self) -> str:
        o = self._op()
        if o is None or not o.escribe:
            return "Esta operación no tiene modo «aplicar»: con F5 se ejecuta."
        return self.motivoNoSimular

    @Property(bool, notify=cambiado)
    def puedeAplicar(self) -> bool:
        return self.motivoNoAplicar == ""

    @Property(str, notify=cambiado)
    def textoConfirmacion(self) -> str:
        o = self._op()
        h = self.herramientas
        if o is None or not o.trabajo or not h.hayActual:
            return ""
        lineas = [f"{'Receta' if h.esReceta else 'Herramienta'}: {h.titulo}", f"Archivos: {self.archivos.resumen}", f"Opciones: {h.textoOpciones}",
                  f"Salida: {h.destinoEfectivo}", "", f"Esta operación {o.toca}."]
        if h.larga:
            lineas.append("Tarda (descargar, transcribir u OCR): verás su progreso en la barra de estado y Esc lo cancela.")
        return "\n".join(lineas)

    # ------------------------------------------------------------------ correr
    @Slot(result=bool)
    def simular(self) -> bool:
        """F5: la herramienta como trabajo simulado, o la CLI de solo lectura."""
        o = self._op()
        if o is None or not self.puedeSimular:
            self.aviso.emit(self.motivoNoSimular, "aviso")
            return False
        if o.trabajo:
            self._encolar(simular=True)
            return True
        return self._lanzar(o, o.cli(list(self.archivos.rutas)))

    @Slot(result=bool)
    def aplicar(self) -> bool:
        """Ctrl+Intro, tras la confirmación en QML."""
        o = self._op()
        if o is None or not self.puedeAplicar:
            self.aviso.emit(self.motivoNoAplicar, "aviso")
            return False
        self._encolar(simular=False)
        return True

    def _encolar(self, simular: bool) -> str:
        h = self.herramientas
        entradas = [] if h.sinArchivos else list(self.archivos.rutas)
        destino = h.destino if h.enCarpeta and h.destino.strip() else ""
        return self.trabajos.encolar(h.ref, h.titulo, entradas, dict(h.valores), destino, simular)

    def _lanzar(self, o: ops.Operacion, orden: ops.Orden) -> bool:
        self._lineas, self._inicio = [], time.monotonic()
        self._worker = self.tareas.proceso(f"Ejecutando: {o.titulo}", list(orden.argv), cwd=str(orden.cwd), entorno={"PYTHONDONTWRITEBYTECODE": "1"},
                                           al_terminar=lambda codigo, i=o.id: self._fin(codigo, i))
        self.cambiado.emit()
        return True

    def _linea(self, texto: str, nivel: str) -> None:
        if self._worker is not None:
            self._lineas.append(texto)

    def _fin(self, codigo: int, id_: str) -> None:
        self._worker = None
        segundos = time.monotonic() - self._inicio
        o = ops.operacion(id_)
        titulo = o.titulo if o else id_
        cuerpo = "\n".join(self._lineas[1:] if self._lineas and self._lineas[0].startswith("$ ") else self._lineas) + "\n"
        self._escribir(id_, f"# {time.strftime('%Y-%m-%d %H:%M:%S')} · {titulo} · código de salida {codigo} · {segundos:.1f} s\n\n{cuerpo}")
        self.aviso.emit(f"{titulo}: {'listo' if codigo == 0 else f'código {codigo}'} ({segundos:.1f} s); la salida está en el panel inferior (F4).",
                        "informacion" if codigo == 0 else "aviso")
        self.cambiado.emit()
        self.corridaCambiada.emit()
        self.terminada.emit(id_, False, codigo)

    @Slot()
    def cancelar(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self.tareas.cancelar()
        elif self.trabajos.enCurso:
            self.trabajos.cancelar()

    def _escribir(self, id_: str, texto: str) -> None:
        try:
            self._cache.mkdir(parents=True, exist_ok=True)
            (self._cache / f"{id_}.txt").write_text(texto, encoding="utf-8")
        except OSError:
            pass

    @Property(str, notify=corridaCambiada)
    def salida(self) -> str:
        """Lo que dejó la última corrida de la CLI de la operación actual."""
        try:
            return (self._cache / f"{self._actual}.txt").read_text(encoding="utf-8")
        except OSError:
            return ""

    # ------------------------------------------------------------------ Dolphin y las carpetas vigiladas
    @Property(bool, notify=cambiado)
    def dolphinInstalado(self) -> bool:
        try:
            from escritorio import dolphin
            return dolphin.hay()
        except Exception:       # noqa: BLE001
            return False

    @Slot(bool, result=bool)
    def instalarDolphin(self, si: bool) -> bool:
        try:
            from escritorio import dolphin
            dolphin.instalar(bool(si))
        except Exception as e:      # noqa: BLE001
            self.aviso.emit(f"No se pudieron {'instalar' if si else 'quitar'} los menús de Dolphin: {e}", "error")
            return False
        self.consola.registrar("ok", "Menús de Dolphin " + ("instalados" if si else "quitados"))
        self.aviso.emit("Menús de Dolphin " + ("instalados." if si else "quitados."), "positivo")
        self.cambiado.emit()
        return True

    def fijar_vigilancia(self, vigilancia) -> None:
        self._vigilancia = vigilancia
        self.cambiado.emit()

    @Property("QVariantList", notify=cambiado)
    def vigiladas(self) -> list:
        return list(self._vigilancia.lista()) if self._vigilancia is not None else []

    @Property("QVariantList", notify=cambiado)
    def recetasParaVigilar(self) -> list:
        return [{"ref": f["ref"], "id": f["id"], "titulo": f["titulo"]} for f in self.herramientas._fichas.values()
                if f.get("es_receta") and f.get("entrada") != "ninguna"]

    @Slot(str, str, result=bool)
    def vigilar(self, carpeta: str, receta: str) -> bool:
        carpeta = (carpeta or "").strip()
        if self._vigilancia is None or not carpeta or not Path(carpeta).is_dir() or not receta:
            self.aviso.emit("Elige una carpeta que exista y una receta.", "aviso")
            return False
        self._vigilancia.vigilar(carpeta, receta)
        self.consola.registrar("ok", f"Carpeta vigilada: {carpeta} → receta {receta}")
        self.aviso.emit(f"Vigilando {rutas.relativa(carpeta)}: lo que llegue pasa por «{receta}».", "positivo")
        self.cambiado.emit()
        return True

    @Slot(str, result=bool)
    def dejarDeVigilar(self, carpeta: str) -> bool:
        if self._vigilancia is None:
            return False
        self._vigilancia.dejar(carpeta)
        self.consola.registrar("info", f"Ya no se vigila: {carpeta}")
        self.cambiado.emit()
        return True

    def entradas_paleta(self, _texto: str) -> list[dict]:
        return [{"nombre": f"op.ir.{o.id}", "texto": f"Operación: {o.titulo}", "grupo": "Operaciones", "icono": o.icono, "ejecutar": lambda i=o.id: self.fijar(i)}
                for o in ops.OPERACIONES]
