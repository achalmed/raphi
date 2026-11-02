"""escritorio/studio/controladores/herramientas.py — la tabla de herramientas (las operaciones del motor y las recetas,
de las fichas del corredor en caché; releídas en segundo plano) filtrada por familia o por los archivos que aceptan;
la herramienta actual con su Resumen (Markdown), los campos de sus Opciones (`PaginaFormulario`, desde la ficha) y
sus valores (recordados por herramienta en QSettings), el destino de la salida (junto a cada original · en una
carpeta); el último trabajo de cada herramienta."""
from __future__ import annotations

import json
from pathlib import Path

from gui_comun.modelos import ModeloFiltrado, ModeloTabla
from gui_comun.qt import QObject, QSettings, QStandardPaths, Property, Signal, Slot

from escritorio.studio import familias
from escritorio.studio.servicios import fichas as svc
from escritorio.studio.servicios import rutas

COLUMNAS = [("Herramienta", "titulo"), ("Familia", "familia_texto"), ("Categoría", "categoria"), ("Acepta", "acepta"), ("Entradas", "entradas"),
            ("Opciones", "opciones"), ("Estado", "estado")]


def cache_del_studio() -> Path:
    return Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.CacheLocation) or (Path.home() / ".cache" / "raphi-studio"))


class Herramientas(QObject):
    cambiado = Signal()                 # la tabla y los contadores
    actualCambiado = Signal()           # la herramienta actual
    opcionesCambiadas = Signal()        # los valores y el destino
    seleccionar = Signal(int)
    aviso = Signal(str, str)

    def __init__(self, espacio, archivos, consola, tareas, cache: Path | None = None, parent=None):
        super().__init__(parent)
        self.espacio, self.archivos, self.consola, self.tareas = espacio, archivos, consola, tareas
        self._s = QSettings()
        self._cache = cache or cache_del_studio()
        self._tabla = ModeloTabla(COLUMNAS, parent=self)
        self._modelo = ModeloFiltrado(self._tabla, parent=self)
        self._datos: dict = {}
        self._fichas: dict[str, dict] = {}
        self._orden: list[str] = []
        self._actual = ""
        self._valores: dict = {}
        self._destino = ""
        self._en_carpeta = False
        self._motivo = ""
        self._modelo.aceptar_con(self._acepta)
        espacio.filtroCambiado.connect(lambda: self._modelo.aceptar_con(self._acepta))
        archivos.cambiado.connect(self._archivos_cambiaron)
        self.cargar_cache()

    modelo = Property(QObject, lambda self: self._modelo, constant=True)

    # ------------------------------------------------------------------ las fichas
    def _archivo_cache(self) -> Path:
        return self._cache / "fichas.json"

    def cargar_cache(self) -> bool:
        datos = svc.leer_cache(self._archivo_cache())
        if datos:
            self._poner(datos)
            return True
        return False

    def _poner(self, datos: dict) -> None:
        self._datos = datos
        lista = svc.herramientas(datos)
        self._fichas = {f["ref"]: f for f in lista}
        self._orden = [f["ref"] for f in lista]
        self._tabla.poner([self._fila(f) for f in lista])
        self.cambiado.emit()
        if self._actual and self._actual not in self._fichas:
            self._fijar_actual("")
        elif self._actual:
            self.actualCambiado.emit()

    def _fila(self, f: dict) -> dict:
        faltan = f.get("faltan") or []
        return {"titulo": f["titulo"], "familia_texto": familias.nombre_de(f["familia"]), "categoria": f.get("categoria", ""), "acepta": svc.acepta_texto(f),
                "entradas": svc.entrada_texto(f).split(" (")[0], "opciones": str(len(f.get("parametros", []))) if not f.get("es_receta") else f"{len(f.get('pasos', []))} pasos",
                "estado": "lista" if not faltan else "falta " + ", ".join(x.removeprefix("py:") for x in faltan), "nivel": "positivo" if not faltan else "negativo",
                "icono": {"titulo": f.get("icono", "")}, "habilitado": True, "ref": f["ref"], "familia": f["familia"], "clave": "lista" if not faltan else "falta",
                "palabras": " ".join(f.get("palabras", [])) + " " + f.get("descripcion", ""),
                "crudo": {"opciones": len(f.get("parametros", [])), "estado": 0 if not faltan else 1}}

    @Slot()
    def releer(self) -> None:
        """Pide las fichas al corredor en segundo plano (F6 y al arrancar); la caché se actualiza al llegar."""
        if self.tareas.activa:
            return

        def trabajo(progress_cb=None, cancel_cb=None, message_cb=None):
            return svc.pedir()

        def listo(datos):
            if not isinstance(datos, dict):
                return
            svc.guardar_cache(self._archivo_cache(), datos)
            self._poner(datos)
            self._motivo = ""
            self.consola.registrar("info", f"Fichas releídas: {len(datos.get('operaciones', []))} operaciones y {len(datos.get('recetas', []))} recetas (Raphi {datos.get('version', '')}, {Path(datos.get('interprete', '')).parent.parent.name or 'motor'})")

        self.tareas.funcion("Leyendo las fichas del motor", trabajo, al_terminar=listo, silenciosa=True)

    def releer_ahora(self) -> bool:
        """Las fichas en este mismo hilo (las pruebas y las capturas)."""
        try:
            datos = svc.pedir()
        except Exception as e:      # noqa: BLE001
            self._motivo = str(e)
            self.consola.registrar("error", f"No se pudieron leer las fichas del motor: {e}")
            self.cambiado.emit()
            return False
        svc.guardar_cache(self._archivo_cache(), datos)
        self._poner(datos)
        return True

    @Property(str, notify=cambiado)
    def version(self) -> str:
        return str(self._datos.get("version", ""))

    @Property(str, notify=cambiado)
    def motivoSinFichas(self) -> str:
        return self._motivo

    # ------------------------------------------------------------------ la tabla
    def _acepta(self, fila_origen: int) -> bool:
        f = self._tabla.fila(fila_origen)
        if self.espacio.familia and f.get("familia") != self.espacio.familia:
            return False
        if self.espacio.soloAceptan:
            ficha = self._fichas.get(f.get("ref", ""))
            return bool(ficha) and familias.acepta(ficha, self.archivos.rutas)
        return True

    def _archivos_cambiaron(self) -> None:
        if self.espacio.soloAceptan:
            self._modelo.aceptar_con(self._acepta)
        self.cambiado.emit()

    @Property(int, notify=cambiado)
    def total(self) -> int:
        return len(self._fichas)

    @Property(int, notify=cambiado)
    def listas(self) -> int:
        return sum(1 for f in self._fichas.values() if not f.get("faltan"))

    @Property("QVariantList", notify=cambiado)
    def faltantes(self) -> list:
        """[{programa, usan: [títulos]}] de lo que falta en esta máquina."""
        por_programa: dict[str, list] = {}
        for f in self._fichas.values():
            for x in f.get("faltan") or []:
                por_programa.setdefault(x, []).append(f["titulo"])
        return [{"programa": p.removeprefix("py:") + (" (módulo de Python del motor)" if p.startswith("py:") else ""), "usan": sorted(set(u))} for p, u in sorted(por_programa.items())]

    @Property(str, notify=cambiado)
    def resumen(self) -> str:
        return f"{self.total} herramientas · {self.listas} listas en esta máquina"

    @Property("QVariantList", notify=cambiado)
    def filasNavegacion(self) -> list:
        filas = [{"nombre": "familia", "texto": "Todas", "icono": "application-x-executable", "contador": len(self._fichas)}]
        for id_, nombre, _p, icono in familias.FAMILIAS:
            n = sum(1 for f in self._fichas.values() if f["familia"] == id_)
            filas.append({"nombre": f"familia.{id_}", "texto": nombre, "icono": icono, "contador": n})
        return filas

    @Property("QVariantList", notify=cambiado)
    def refs(self) -> list:
        return list(self._orden)

    @Slot(str, result="QVariantMap")
    def ficha(self, ref: str) -> dict:
        return dict(self._fichas.get(ref, {}))

    @Slot(result="QVariantList")
    def queAceptan(self) -> list:
        """Las referencias de las herramientas que sirven para los archivos de la lista."""
        return [r for r in self._orden if familias.acepta(self._fichas[r], self.archivos.rutas)]

    # ------------------------------------------------------------------ la herramienta actual
    @Slot(int)
    def fijarFila(self, fila: int) -> None:
        if fila < 0 or fila >= self._modelo.rowCount():
            return
        self._fijar_actual(self._tabla.fila(self._modelo.filaOrigen(fila)).get("ref", ""))

    @Slot(str, result=int)
    def filaDe(self, ref: str) -> int:
        for i, f in enumerate(self._tabla.todas()):
            if f.get("ref") == ref:
                return self._modelo.filaVisible(i)
        return -1

    @Slot(str, result=bool)
    def irA(self, ref: str) -> bool:
        if ref not in self._fichas:
            return False
        self.espacio.fijarVista("herramientas")
        if self.filaDe(ref) < 0:
            self.espacio.fijarSoloAceptan(False)
            self.espacio.fijarFamilia("")
        self._fijar_actual(ref)
        self.seleccionar.emit(self.filaDe(ref))
        return True

    def _fijar_actual(self, ref: str) -> None:
        if ref == self._actual:
            return
        self._actual = ref if ref in self._fichas else ""
        self._valores = self._leer_valores()
        self._en_carpeta = str(self._s.value(f"salida/{self._actual}/en_carpeta", "false")).lower() == "true" if self._actual else False
        self._destino = str(self._s.value(f"salida/{self._actual}/carpeta", "") or "") if self._actual else ""
        self.actualCambiado.emit()
        self.opcionesCambiadas.emit()

    def _ficha_actual(self) -> dict:
        return self._fichas.get(self._actual, {})

    @Property(bool, notify=actualCambiado)
    def hayActual(self) -> bool:
        return bool(self._actual)

    @Property(str, notify=actualCambiado)
    def ref(self) -> str:
        return self._actual

    @Property(str, notify=actualCambiado)
    def id(self) -> str:
        return self._ficha_actual().get("id", "")

    @Property(str, notify=actualCambiado)
    def titulo(self) -> str:
        return self._ficha_actual().get("titulo", "")

    @Property(str, notify=actualCambiado)
    def descripcion(self) -> str:
        return self._ficha_actual().get("descripcion", "")

    @Property(str, notify=actualCambiado)
    def icono(self) -> str:
        return self._ficha_actual().get("icono", "")

    @Property(str, notify=actualCambiado)
    def familia(self) -> str:
        return self._ficha_actual().get("familia", "")

    @Property(str, notify=actualCambiado)
    def textoFamilia(self) -> str:
        return familias.nombre_de(self.familia) if self._actual else ""

    @Property(bool, notify=actualCambiado)
    def esReceta(self) -> bool:
        return bool(self._ficha_actual().get("es_receta"))

    @Property(bool, notify=actualCambiado)
    def larga(self) -> bool:
        return bool(self._ficha_actual().get("larga"))

    @Property(bool, notify=actualCambiado)
    def sinArchivos(self) -> bool:
        f = self._ficha_actual()
        return bool(f) and (f.get("entrada") == "ninguna" or f.get("minimo_entradas", 1) == 0)

    @Property(int, notify=actualCambiado)
    def minimoEntradas(self) -> int:
        return int(self._ficha_actual().get("minimo_entradas", 1)) if self._actual else 0

    @Property("QVariantList", notify=actualCambiado)
    def faltan(self) -> list:
        return [x.removeprefix("py:") for x in self._ficha_actual().get("faltan") or []]

    @Property(str, notify=actualCambiado)
    def textoAcepta(self) -> str:
        return svc.acepta_texto(self._ficha_actual()) if self._actual else ""

    @Property(str, notify=actualCambiado)
    def resumenMarkdown(self) -> str:
        return svc.resumen_markdown(self._ficha_actual()) if self._actual else ""

    @Property("QVariantList", notify=actualCambiado)
    def campos(self) -> list:
        return svc.campos_formulario(self._ficha_actual()) if self._actual else []

    @Property(bool, notify=actualCambiado)
    def aceptaLosArchivos(self) -> bool:
        return bool(self._actual) and familias.acepta(self._ficha_actual(), self.archivos.rutas)

    @Property(str, notify=actualCambiado)
    def extensionesFiltro(self) -> str:
        ext = self._ficha_actual().get("extensiones") or []
        return " ".join(f"*{e}" for e in ext)

    # ------------------------------------------------------------------ las opciones
    def _leer_valores(self) -> dict:
        if not self._actual:
            return {}
        try:
            return dict(json.loads(str(self._s.value(f"opciones/{self._actual}", "") or "{}")))
        except (ValueError, TypeError):
            return {}

    @Property("QVariantMap", notify=opcionesCambiadas)
    def valores(self) -> dict:
        return dict(self._valores)

    @Slot(str, "QVariant")
    def fijarValor(self, clave: str, valor) -> None:
        if not self._actual:
            return
        if valor in ("", None):
            self._valores.pop(clave, None)
        else:
            self._valores[clave] = valor
        self._s.setValue(f"opciones/{self._actual}", json.dumps(self._valores, ensure_ascii=False, default=str))
        self.opcionesCambiadas.emit()

    @Slot()
    def restablecerOpciones(self) -> None:
        if self._actual:
            self._valores = {}
            self._s.remove(f"opciones/{self._actual}")
            self.opcionesCambiadas.emit()

    @Property(bool, notify=opcionesCambiadas)
    def enCarpeta(self) -> bool:
        return self._en_carpeta

    @Slot(bool)
    def fijarEnCarpeta(self, v: bool) -> None:
        if self._actual and bool(v) != self._en_carpeta:
            self._en_carpeta = bool(v)
            self._s.setValue(f"salida/{self._actual}/en_carpeta", "true" if v else "false")
            self.opcionesCambiadas.emit()

    @Property(str, notify=opcionesCambiadas)
    def destino(self) -> str:
        return self._destino

    @Slot(str)
    def fijarDestino(self, ruta: str) -> None:
        ruta = (ruta or "").strip()
        if self._actual and ruta != self._destino:
            self._destino = ruta
            self._s.setValue(f"salida/{self._actual}/carpeta", ruta)
            if ruta:
                self._en_carpeta = True
                self._s.setValue(f"salida/{self._actual}/en_carpeta", "true")
            self.opcionesCambiadas.emit()

    @Property(str, notify=opcionesCambiadas)
    def destinoEfectivo(self) -> str:
        if self._en_carpeta and self._destino:
            return self._destino
        if self.sinArchivos:
            return str(rutas.carpeta_descargas())
        return "junto a cada original"

    @Property(str, notify=opcionesCambiadas)
    def textoOpciones(self) -> str:
        if not self._valores:
            return "las de por omisión"
        return ", ".join(f"{k} = {v}" for k, v in self._valores.items())

    def entradas_paleta(self, _texto: str) -> list[dict]:
        return [{"nombre": f"herramienta.{f['ref']}", "texto": f["titulo"], "grupo": familias.nombre_de(f["familia"]), "icono": f.get("icono", ""),
                 "ejecutar": lambda r=f["ref"]: self.irA(r)} for f in self._fichas.values()]
