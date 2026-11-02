"""escritorio/studio/controladores/trabajos.py — la cola de trabajos del studio (`docs/rediseno.md` S3): encolar un
trabajo (la herramienta sobre los archivos con las opciones, simulado o de verdad), correr el siguiente con
`gui_comun.tareas.proceso` (el corredor en el intérprete del motor; uno a la vez; el progreso de sus líneas
`## progreso`; Esc cancela), leer su informe al terminar; la tabla de trabajos filtrada por grupo; el trabajo actual con
su Resumen, su Resultado (Markdown; las salidas con vista previa) y su Registro; la lista persistida en la caché."""
from __future__ import annotations

import json
import time
from pathlib import Path

from gui_comun.modelos import ModeloFiltrado, ModeloTabla
from gui_comun.qt import QObject, Property, Signal, Slot

from escritorio.studio.servicios import archivos as svc_archivos
from escritorio.studio.servicios import rutas
from escritorio.studio.servicios import trabajos as svc

COLUMNAS = [("Trabajo", "titulo"), ("Archivos", "archivos"), ("Estado", "estado"), ("Progreso", "progreso"), ("Inicio", "inicio"), ("Duración", "duracion"),
            ("Salidas", "salidas")]
COLUMNAS_SALIDAS = [("Salida", "nombre"), ("Tipo", "tipo"), ("Tamaño", "tamano"), ("Carpeta", "carpeta")]


def _hora(ts: float) -> str:
    return time.strftime("%H:%M:%S", time.localtime(ts)) if ts else "—"


def _duracion(segundos: float) -> str:
    if segundos <= 0:
        return "—"
    if segundos < 60:
        return f"{segundos:.1f} s"
    return f"{int(segundos // 60)} min {int(segundos % 60)} s"


class Trabajos(QObject):
    cambiado = Signal()                 # la tabla y los contadores
    actualCambiado = Signal()
    terminado = Signal(str, bool, str)  # id, simulado, estado
    seleccionar = Signal(int)
    aviso = Signal(str, str)

    def __init__(self, espacio, herramientas, consola, tareas, cache: Path | None = None, parent=None):
        super().__init__(parent)
        self.espacio, self.herramientas, self.consola, self.tareas = espacio, herramientas, consola, tareas
        self._cache = cache or herramientas._cache
        self._lista = svc.Lista(self._cache / "trabajos.json")
        self._tabla = ModeloTabla(COLUMNAS, parent=self)
        self._modelo = ModeloFiltrado(self._tabla, parent=self)
        self._salidas = ModeloTabla(COLUMNAS_SALIDAS, parent=self)
        self._actual = ""
        self._en_curso: svc.Trabajo | None = None
        self._lineas: list[str] = []
        self._worker = None
        self._cancelando = False
        self._salida_fila = -1
        self._modelo.aceptar_con(self._acepta)
        espacio.filtroCambiado.connect(lambda: self._modelo.aceptar_con(self._acepta))
        tareas.linea.connect(self._linea)
        self._tabla.poner([self._fila(t) for t in self._lista.trabajos])
        self.cambiado.emit()

    modelo = Property(QObject, lambda self: self._modelo, constant=True)
    salidasModelo = Property(QObject, lambda self: self._salidas, constant=True)

    # ------------------------------------------------------------------ la tabla
    def _acepta(self, fila_origen: int) -> bool:
        f = self._tabla.fila(fila_origen)
        return self.espacio.grupo == "todos" or f.get("grupo") == self.espacio.grupo

    def _fila(self, t: svc.Trabajo) -> dict:
        n = len(t.archivos)
        archivos = (Path(t.archivos[0]).name + (f" y {n - 1} más" if n > 1 else "")) if n else "—"
        return {"titulo": t.titulo + (" (simulación)" if t.simular else ""), "archivos": archivos, "estado": svc.TEXTO_DE_ESTADO[t.estado],
                "progreso": f"{t.progreso} %" if t.estado == "en_curso" else ("100 %" if t.estado == "hecho" else "—"), "inicio": _hora(t.inicio or t.creado),
                "duracion": _duracion(t.duracion) if t.estado not in ("en_cola",) else "—", "salidas": str(len(t.salidas)) if t.salidas else ("plan" if t.simular and t.estado == "hecho" else "—"),
                "nivel": svc.NIVEL_DE_ESTADO[t.estado], "icono": {"titulo": svc.ICONO_DE_ESTADO[t.estado]}, "habilitado": True, "id": t.id, "grupo": t.grupo,
                "ref": t.ref, "crudo": {"inicio": t.inicio or t.creado, "duracion": t.duracion, "salidas": len(t.salidas), "progreso": t.progreso}}

    def _refrescar(self, t: svc.Trabajo) -> None:
        for i, f in enumerate(self._tabla.todas()):
            if f.get("id") == t.id:
                self._tabla.actualizar(i, **self._fila(t))
                break
        self.cambiado.emit()
        if t.id == self._actual:
            self.actualCambiado.emit()

    @Property(int, notify=cambiado)
    def total(self) -> int:
        return len(self._lista.trabajos)

    @Property("QVariantMap", notify=cambiado)
    def contadores(self) -> dict:
        return self._lista.contar()

    @Property(str, notify=cambiado)
    def resumen(self) -> str:
        c = self._lista.contar()
        if not c["todos"]:
            return "sin trabajos"
        return f"{c['todos']} trabajos: {c['en_cola']} en cola · {c['en_curso']} en curso · {c['hechos']} hechos · {c['con_error']} con error"

    @Property("QVariantList", notify=cambiado)
    def filasNavegacion(self) -> list:
        c = self._lista.contar()
        iconos = {"todos": "view-task", "en_cola": "chronometer", "en_curso": "media-playback-start", "hechos": "data-success", "con_error": "data-error"}
        return [{"nombre": "trabajos" if g == "todos" else f"trabajos.{g}", "texto": t, "icono": iconos[g], "contador": c.get(g, 0)} for g, t in svc.GRUPOS]

    @Property(bool, notify=cambiado)
    def enCurso(self) -> bool:
        return self._en_curso is not None

    @Property(str, notify=cambiado)
    def textoEnCurso(self) -> str:
        t = self._en_curso
        return f"{t.titulo} · {t.progreso} %" + (f" · {t.mensaje}" if t.mensaje else "") if t else ""

    # ------------------------------------------------------------------ encolar y correr
    def encolar(self, ref: str, titulo: str, archivos: list[str], params: dict, destino: str, simular: bool) -> str:
        t = svc.nuevo(ref, titulo, archivos, params, destino, simular)
        self._lista.anadir(t)
        self._tabla.anadir(self._fila(t))
        self.consola.registrar("info", f"Trabajo {'simulado' if simular else 'nuevo'}: {titulo} ({len(archivos)} archivo(s))")
        self.cambiado.emit()
        self._fijar_actual(t.id)
        self._siguiente()
        return t.id

    def _siguiente(self) -> None:
        if self._en_curso is not None or self.tareas.activa:
            return
        t = self._lista.siguiente_en_cola()
        if t is None:
            return
        self._en_curso, self._lineas, self._cancelando = t, [], False
        t.estado, t.inicio, t.progreso, t.mensaje = "en_curso", time.time(), 0, ""
        archivo = self._cache / "trabajos" / f"{t.id}.json"
        try:
            archivo.parent.mkdir(parents=True, exist_ok=True)
            archivo.write_text(json.dumps(t.para_corredor(), ensure_ascii=False), encoding="utf-8")
        except OSError as e:
            self._terminar(2, cancelado=False, error=f"No se pudo escribir el trabajo: {e}")
            return
        argv = [rutas.interprete_motor(), str(rutas.CORREDOR), "ejecutar", str(archivo)]
        nombre = f"{'Simulando' if t.simular else 'Aplicando'}: {t.titulo}"
        self._worker = self.tareas.proceso(nombre, argv, cwd=str(rutas.REPO), entorno={"PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1"},
                                           progreso_de=self._progreso, al_terminar=lambda codigo: self._terminar(codigo, cancelado=self._cancelando))
        self._refrescar(t)

    def _progreso(self, linea: str):
        p = svc.progreso_de(linea)
        if p and self._en_curso is not None:
            self._en_curso.progreso, self._en_curso.mensaje = p[0], p[1]
            self._refrescar(self._en_curso)
        return p

    def _linea(self, texto: str, nivel: str) -> None:
        if self._en_curso is not None:
            self._lineas.append(texto)

    def _terminar(self, codigo: int, cancelado: bool, error: str = "") -> None:
        t = self._en_curso
        self._en_curso, self._worker = None, None
        if t is None:
            return
        t.fin, t.codigo = time.time(), codigo
        lineas = self._lineas[1:] if self._lineas and self._lineas[0].startswith("$ ") else self._lineas      # sin la orden que la consola anuncia
        t.registro = "\n".join(l for l in lineas if not l.startswith("## ")) + "\n"
        informe = svc.informe_de(self._lineas)
        if error:
            t.estado, t.mensaje, t.informe = "fallido", error, {"ok": False, "error": error, "elementos": []}
        else:
            t.informe = informe or {}
            t.estado, t.mensaje = svc.estado_final(codigo, informe, cancelado)
            t.salidas = [a for e in (informe or {}).get("elementos", []) for a in e.get("archivos", [])]
        t.progreso = 100 if t.estado == "hecho" else t.progreso
        self._lista.guardar()
        if t.id == self._actual:
            self._fijar_actual(t.id)                 # las salidas y su vista previa
        self._refrescar(t)
        if t.estado == "hecho":
            self.aviso.emit(f"{t.titulo}{' (simulación)' if t.simular else ''}: {t.mensaje}" + (" · revisa el plan y aplica con Ctrl+Intro." if t.simular else "."),
                            "informacion" if t.simular else "positivo")
        else:
            self.aviso.emit(f"{t.titulo}: {t.mensaje}", "aviso" if t.estado == "cancelado" else "error")
        self.terminado.emit(t.id, t.simular, t.estado)
        self._siguiente()

    @Slot()
    def cancelar(self) -> None:
        if self._en_curso is not None:
            self._cancelando = True
            self.tareas.cancelar()

    @Slot(str)
    def quitarDeLaCola(self, ident: str) -> None:
        t = self._lista.por_id(ident)
        if t and t.estado == "en_cola":
            t.estado, t.mensaje, t.fin = "cancelado", "Quitado de la cola.", time.time()
            self._lista.guardar()
            self._refrescar(t)

    @Slot()
    def limpiarHechos(self) -> None:
        """Quita de la lista los trabajos terminados (las salidas no se tocan)."""
        self._lista.trabajos = [t for t in self._lista.trabajos if t.estado in ("en_cola", "en_curso")]
        self._lista.guardar()
        self._tabla.poner([self._fila(t) for t in self._lista.trabajos])
        if self._actual and not self._lista.por_id(self._actual):
            self._fijar_actual("")
        self.cambiado.emit()

    # ------------------------------------------------------------------ el trabajo actual
    @Slot(int)
    def fijarFila(self, fila: int) -> None:
        if fila < 0 or fila >= self._modelo.rowCount():
            return
        self._fijar_actual(self._tabla.fila(self._modelo.filaOrigen(fila)).get("id", ""))

    @Slot(str, result=int)
    def filaDe(self, ident: str) -> int:
        for i, f in enumerate(self._tabla.todas()):
            if f.get("id") == ident:
                return self._modelo.filaVisible(i)
        return -1

    @Slot(str, result=bool)
    def irA(self, ident: str) -> bool:
        if not self._lista.por_id(ident):
            return False
        self.espacio.fijarVista("trabajos")
        if self.filaDe(ident) < 0:
            self.espacio.fijarGrupo("todos")
        self._fijar_actual(ident)
        self.seleccionar.emit(self.filaDe(ident))
        return True

    def _fijar_actual(self, ident: str) -> None:
        self._actual = ident if self._lista.por_id(ident) else ""
        t = self._t()
        self._salidas.poner([svc_archivos.fila_de(a) for a in (t.salidas if t else [])])
        self._salida_fila = 0 if t and t.salidas else -1
        self.actualCambiado.emit()

    def _t(self) -> svc.Trabajo | None:
        return self._lista.por_id(self._actual) if self._actual else None

    @Slot(str, result="QVariantMap")
    def ultimoDe(self, ref: str) -> dict:
        """El último trabajo de una herramienta (para su pestaña Resultado)."""
        for t in reversed(self._lista.trabajos):
            if t.ref == ref:
                return {"id": t.id, "estado": t.estado, "texto": svc.TEXTO_DE_ESTADO[t.estado], "simular": t.simular, "mensaje": t.mensaje,
                        "resultado": svc.texto_resultado(t), "salidas": list(t.salidas), "fin": _hora(t.fin)}
        return {}

    @Slot(str)
    def irAlUltimoDe(self, ref: str) -> None:
        for t in reversed(self._lista.trabajos):
            if t.ref == ref:
                self._fijar_actual(t.id)
                return
        self._fijar_actual("")

    @Property(bool, notify=actualCambiado)
    def hayActual(self) -> bool:
        return self._t() is not None

    @Property(str, notify=actualCambiado)
    def id(self) -> str:
        return self._actual

    @Property(str, notify=actualCambiado)
    def titulo(self) -> str:
        t = self._t()
        return t.titulo if t else ""

    @Property(str, notify=actualCambiado)
    def ref(self) -> str:
        t = self._t()
        return t.ref if t else ""

    @Property(str, notify=actualCambiado)
    def estado(self) -> str:
        t = self._t()
        return t.estado if t else ""

    @Property(str, notify=actualCambiado)
    def textoEstado(self) -> str:
        t = self._t()
        return svc.TEXTO_DE_ESTADO[t.estado] if t else ""

    @Property(str, notify=actualCambiado)
    def nivelEstado(self) -> str:
        t = self._t()
        return svc.NIVEL_DE_ESTADO[t.estado] if t else ""

    @Property(bool, notify=actualCambiado)
    def simulado(self) -> bool:
        t = self._t()
        return bool(t and t.simular)

    @Property(int, notify=actualCambiado)
    def progreso(self) -> int:
        t = self._t()
        return t.progreso if t else 0

    @Property(str, notify=actualCambiado)
    def mensaje(self) -> str:
        t = self._t()
        return t.mensaje if t else ""

    @Property("QVariantList", notify=actualCambiado)
    def archivos(self) -> list:
        t = self._t()
        return list(t.archivos) if t else []

    @Property(str, notify=actualCambiado)
    def textoArchivos(self) -> str:
        t = self._t()
        if not t:
            return ""
        return ", ".join(Path(a).name for a in t.archivos[:4]) + (f" y {len(t.archivos) - 4} más" if len(t.archivos) > 4 else "") if t.archivos else "sin archivos"

    @Property(str, notify=actualCambiado)
    def textoOpciones(self) -> str:
        t = self._t()
        return (", ".join(f"{k} = {v}" for k, v in t.params.items()) or "las de por omisión") if t else ""

    @Property(str, notify=actualCambiado)
    def destino(self) -> str:
        t = self._t()
        return (t.destino or "junto a cada original") if t else ""

    @Property(str, notify=actualCambiado)
    def inicio(self) -> str:
        t = self._t()
        return _hora(t.inicio or t.creado) if t else ""

    @Property(str, notify=actualCambiado)
    def duracion(self) -> str:
        t = self._t()
        return _duracion(t.duracion) if t and t.estado != "en_cola" else ""

    @Property(str, notify=actualCambiado)
    def resultado(self) -> str:
        t = self._t()
        return svc.texto_resultado(t) if t else ""

    @Property(str, notify=actualCambiado)
    def registro(self) -> str:
        t = self._t()
        return t.registro if t else ""

    @Property("QVariantList", notify=actualCambiado)
    def salidas(self) -> list:
        t = self._t()
        return list(t.salidas) if t else []

    @Property(int, notify=actualCambiado)
    def nSalidas(self) -> int:
        t = self._t()
        return len(t.salidas) if t else 0

    # ------------------------------------------------------------------ la vista previa de una salida
    @Slot(int)
    def fijarSalida(self, fila: int) -> None:
        self._salida_fila = fila
        self.actualCambiado.emit()

    @Property(str, notify=actualCambiado)
    def salidaActual(self) -> str:
        t = self._t()
        return t.salidas[self._salida_fila] if t and 0 <= self._salida_fila < len(t.salidas) else ""

    @Property(str, notify=actualCambiado)
    def vistaPrevia(self) -> str:
        return svc_archivos.vista_previa(self.salidaActual) if self.salidaActual else ""

    @Property(str, notify=actualCambiado)
    def textoSalida(self) -> str:
        return svc_archivos.leer_texto(self.salidaActual) if self.vistaPrevia == "texto" else ""

    @Property(str, notify=actualCambiado)
    def imagenSalida(self) -> str:
        return Path(self.salidaActual).as_uri() if self.vistaPrevia == "imagen" else ""

    def entradas_paleta(self, _texto: str) -> list[dict]:
        return [{"nombre": f"trabajo.{t.id}", "texto": f"Trabajo: {t.titulo} · {svc.TEXTO_DE_ESTADO[t.estado]}", "grupo": "Trabajos",
                 "icono": svc.ICONO_DE_ESTADO[t.estado], "ejecutar": lambda i=t.id: self.irA(i)} for t in reversed(self._lista.trabajos[-20:])]
