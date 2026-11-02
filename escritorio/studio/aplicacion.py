"""escritorio/studio/aplicacion.py — arma Raphi Studio: la aplicación (gui_comun.nucleo), los controladores, el registro
de acciones (menú, barra, menú contextual, paleta, atajos), la instancia única (los archivos que llegan de Dolphin o
de otra instancia van a la ventana abierta) y carga `qml/Main.qml`.

Reingeniería del 2026-11-02 (`docs/reingenieria.md`): un estudio multimedia, no un explorador — el catálogo de
herramientas en cuadrícula por áreas, el espacio de trabajo de cada herramienta (entradas, vista previa, opciones) y la
cola. Toda operación existe una sola vez, aquí, en `Acciones`: F5 simula (la herramienta sobre las entradas como
trabajo simulado del corredor) y Ctrl+Intro procesa tras la confirmación de gui-comun 3.0. Lo que necesita
un diálogo lo pide a QML por `Interfaz.pedir`. Python no construye interfaz; el motor corre como proceso con el
`.venv` del repo (`corredor.py`); la ventana no nombra ninguna operación (lo vigila `tests/test_studio.py`).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from escritorio.studio import APP_NAME, ORG_NAME, hay_gui_comun

if not hay_gui_comun():
    raise ImportError("falta gui_comun: pip install gui-comun, o GUI_COMUN_DIR con la carpeta del repo gui-comun")

from gui_comun.acciones import Acciones, StandardKey  # noqa: E402
from gui_comun.consola import Consola  # noqa: E402
from gui_comun.nucleo import Aplicacion  # noqa: E402
from gui_comun.qt import QObject, Signal, Slot  # noqa: E402
from gui_comun.tareas import Tareas  # noqa: E402

from escritorio.studio import familias  # noqa: E402
from escritorio.studio.controladores.ajustes import Ajustes  # noqa: E402
from escritorio.studio.controladores.archivos import Archivos  # noqa: E402
from escritorio.studio.controladores import espacio as espacio_mod  # noqa: E402
from escritorio.studio.controladores.espacio import Espacio  # noqa: E402
from escritorio.studio.controladores.herramientas import Herramientas  # noqa: E402
from escritorio.studio.controladores.operaciones import Operaciones  # noqa: E402
from escritorio.studio.controladores.trabajos import Trabajos  # noqa: E402
from escritorio.studio.controladores.vista import Vista  # noqa: E402
from escritorio.studio.servicios import operaciones as ops  # noqa: E402
from escritorio.studio.servicios import rutas  # noqa: E402

APP_DIR = Path(__file__).resolve().parent
QML_DIR = APP_DIR / "qml"
RECURSOS_DIR = APP_DIR / "recursos"
REPO = rutas.REPO
APP_ID = "raphi"
NOMBRE = APP_NAME
NOMBRE_SOCKET = "raphi-escritorio"          # el mismo que la ventana web: Dolphin y la CLI no saben cuál está abierta
DESCRIPCION = ("Un estudio de documentos, PDF, imágenes, audio y vídeo en tu máquina: el catálogo de herramientas del motor de Raphi por áreas "
               "con lo que les falta, el espacio de trabajo de cada una (entradas, vista previa, opciones generadas de su ficha) y la cola de trabajos "
               "con su progreso, su resultado, su registro y repetir. F5 simula (el plan: qué se producirá y dónde) y Ctrl+Intro procesa tras confirmar; el "
               "original nunca se toca. El motor corre como proceso con el entorno del repo; la misma herramienta está en la CLI (raphi), en la web y en Qillqa.")
ACENTO = "violeta"


def datos_lanzador() -> dict:
    return dict(app_id=APP_ID, nombre=NOMBRE, comentario="Documentos, PDF, imágenes, audio y video", orden=[str(REPO / "run.sh"), "escritorio"],
                logo_svg=(RECURSOS_DIR / "marca.svg").read_text(encoding="utf-8"), acento=ACENTO, categorias="Office;",
                palabras="pdf;convertir;comprimir;ocr;audio;video;transcribir;whisper;imagen;fotos;", archivos=True)


class Interfaz(QObject):
    pedir = Signal(str, "QVariantMap")

    @Slot(str)
    def abrir(self, nombre: str) -> None:
        self.pedir.emit(nombre, {})


def construir(app: Aplicacion, cache: Path | None = None, releer: bool = True) -> dict:
    """Crea controladores y acciones, y los expone al QML. Devuelve lo creado (para las pruebas y las capturas)."""
    consola = Consola()
    tareas = Tareas(consola)
    interfaz = Interfaz()
    ajustes = Ajustes()
    espacio = Espacio(consola, ajustes, escritorio=getattr(app, "escritorio", None))
    archivos = Archivos(consola)
    herramientas = Herramientas(espacio, archivos, consola, tareas, cache=cache)
    trabajos = Trabajos(espacio, herramientas, consola, tareas, cache=cache)
    operaciones = Operaciones(espacio, herramientas, archivos, trabajos, consola, tareas, cache=cache)
    vista = Vista(herramientas._cache)
    acciones = Acciones()
    acciones.estandar(NOMBRE)
    pedir = lambda que, **datos: (lambda *_: interfaz.pedir.emit(que, datos))

    def objetivo() -> str:
        """Sobre qué actúan abrir, mostrar en Dolphin, terminal y copiar: lo que muestra la vista previa, la salida del
        trabajo elegido en la cola o el archivo elegido de la lista."""
        if espacio.vista == "cola":
            return trabajos.salidaActual or (trabajos.archivos[0] if trabajos.archivos else "")
        return vista.ruta or archivos.rutaActual or (archivos.rutas[0] if archivos.rutas else "")

    # --- Archivo
    acciones.registrar("archivo.anadir", "&Añadir archivos…", "document-open", StandardKey.Open, "Archivo", al_disparar=pedir("elegir_archivos"),
                       descripcion="Archivos de entrada, con el diálogo de KDE (también se sueltan desde Dolphin sobre la ventana)")
    acciones.registrar("archivo.anadir_carpeta", "Añadir una &carpeta…", "folder-open", "Ctrl+Shift+O", "Archivo", al_disparar=pedir("elegir_carpeta"),
                       descripcion="Una carpeta entera como entrada (las herramientas que trabajan con carpetas)")
    acciones.registrar("archivo.quitar", "&Quitar de las entradas", "list-remove", "Delete", "Archivo", habilitada=False, al_disparar=pedir("quitar_archivos"))
    acciones.registrar("archivo.vaciar", "&Vaciar las entradas", "edit-clear-list", None, "Archivo", habilitada=False, al_disparar=lambda *_: archivos.vaciar())
    acciones.registrar("archivo.abrir", "A&brir con su aplicación", "document-open", None, "Archivo", habilitada=False,
                       al_disparar=lambda *_: espacio.abrir(objetivo()), descripcion="El archivo de la vista previa (o la salida elegida) con la aplicación de KDE")
    acciones.registrar("archivo.mostrar", "&Mostrar en Dolphin", "system-file-manager", "Ctrl+Shift+M", "Archivo", habilitada=False,
                       al_disparar=lambda *_: espacio.mostrarEnCarpeta(objetivo()), descripcion="Dolphin en su carpeta, con el archivo señalado")
    acciones.registrar("archivo.terminal", "Abrir &terminal aquí", "utilities-terminal", "Shift+F4", "Archivo", habilitada=False,
                       al_disparar=lambda *_: espacio.abrirTerminal(objetivo()))
    acciones.registrar("archivo.copiar", "Copiar la &ruta", "edit-copy", "Ctrl+Shift+C", "Archivo", habilitada=False, al_disparar=lambda *_: espacio.copiar(objetivo()))
    # --- Editar
    acciones.registrar("editar.buscar", "&Buscar una herramienta", "edit-find", StandardKey.Find, "Editar", al_disparar=pedir("buscar"),
                       descripcion="Por su nombre, lo que hace o sus formatos")
    # --- Ver
    for i, (nombre, texto, icono) in enumerate(espacio_mod.VISTAS, start=1):
        acciones.registrar(f"ver.{nombre}", f"&{i} {texto}", icono, f"Ctrl+{i}", "Ver", marcable=True, al_disparar=lambda *_, n=nombre: espacio.fijarVista(n))
    acciones.registrar("ver.atras", "&Volver al catálogo", "go-previous", "Alt+Left", "Ver", al_disparar=lambda *_: espacio.fijarVista("catalogo"))
    acciones.registrar("ver.area", "&Todas las áreas", "view-grid", "Ctrl+0", "Ver › Área", marcable=True, al_disparar=lambda *_: espacio.fijarArea(""))
    for id_, nombre, _p, icono in familias.AREAS:
        acciones.registrar(f"ver.area.{id_}", f"&{nombre}", icono, None, "Ver › Área", marcable=True, al_disparar=lambda *_, n=id_: espacio.fijarArea(n))
    acciones.registrar("ver.aceptan", "Solo las que &aceptan las entradas", "view-filter", "Ctrl+Shift+A", "Ver", marcable=True,
                       al_disparar=lambda *_: espacio.fijarSoloAceptan(acciones.accion("ver.aceptan").marcada),
                       descripcion="El catálogo se queda con las herramientas que sirven para los archivos de entrada")
    acciones.registrar("ver.releer", "&Releer las fichas", "view-refresh", "F6", "Ver", al_disparar=lambda *_: herramientas.releer(), operacion="lectura",
                       descripcion="Vuelve a pedir al motor sus operaciones, recetas y lo que falta en esta máquina")
    # --- Herramienta
    acciones.registrar("op.simular", "&Simular", "system-run", StandardKey.Refresh, "Herramienta", al_disparar=operaciones.simular, operacion="simulacion",
                       descripcion="La herramienta sobre las entradas sin escribir nada: el plan (qué se producirá y dónde) en la cola")
    acciones.registrar("op.aplicar", "&Procesar…", "media-playback-start", "Ctrl+Return", "Herramienta", habilitada=False, al_disparar=operaciones.aplicar,
                       operacion="escritura", confirmar=True, consecuencias=lambda: operaciones.textoConfirmacion or "Procesa las entradas con la herramienta.",
                       descripcion="Muestra la herramienta, las entradas, las opciones y la salida; si confirmas, el trabajo va a la cola de verdad")
    acciones.registrar("op.cancelar", "&Detener el trabajo", "process-stop", "Escape", "Herramienta", habilitada=False, al_disparar=operaciones.cancelar,
                       descripcion="Detiene el trabajo en curso (también el programa que esté corriendo)")
    acciones.registrar("herramienta.restablecer", "&Restablecer las opciones", "edit-undo", "Ctrl+Shift+R", "Herramienta", habilitada=False,
                       al_disparar=lambda *_: herramientas.restablecerOpciones(), descripcion="Vuelve a las opciones por omisión de la herramienta")
    # --- Cola
    acciones.registrar("trabajos.repetir", "&Repetir el trabajo", "view-refresh", None, "Cola", habilitada=False,
                       al_disparar=lambda *_: trabajos.repetir(trabajos.id), descripcion="El mismo trabajo (entradas, opciones y salida) otra vez a la cola")
    acciones.registrar("trabajos.quitar", "&Quitar de la cola", "list-remove", None, "Cola", habilitada=False, al_disparar=lambda *_: trabajos.quitarDeLaCola(trabajos.id))
    acciones.registrar("trabajos.limpiar", "&Limpiar los terminados", "edit-clear-history", None, "Cola", al_disparar=lambda *_: trabajos.limpiarHechos(),
                       descripcion="Quita de la lista los trabajos hechos, fallidos y cancelados; las salidas no se tocan")
    acciones.registrar("trabajos.herramienta", "Ir a su &herramienta", "go-jump", None, "Cola", habilitada=False, al_disparar=lambda *_: herramientas.irA(trabajos.ref))
    # --- Herramientas (del motor y del escritorio)
    for o in ops.OPERACIONES:
        if o.id == "herramienta":
            continue
        acciones.registrar(f"op.{o.id}", o.titulo, o.icono, None, "Herramientas", operacion="lectura", descripcion=o.descripcion,
                           al_disparar=lambda *_, i=o.id: (operaciones.fijar(i), operaciones.simular(), operaciones.fijar("herramienta"),
                                                          interfaz.pedir.emit("salida", {})))
    acciones.registrar("herr.dolphin", "Menús de &Dolphin…", "system-file-manager", None, "Herramientas", al_disparar=pedir("dolphin"),
                       descripcion="Instalar o quitar «Raphi ▸ …» del clic derecho de Dolphin")
    acciones.registrar("herr.vigilar", "Carpetas &vigiladas…", "folder-sync", None, "Herramientas", al_disparar=pedir("vigilar"),
                       descripcion="Una carpeta cuyo contenido nuevo pasa por una receta")
    acciones.registrar("herr.faltan", "Lo que &falta en esta máquina…", "dialog-warning", None, "Herramientas", al_disparar=pedir("faltan"))
    acciones.registrar("herr.salida", "&Salida del motor", "utilities-terminal", "F4", "Herramientas", al_disparar=pedir("salida"),
                       descripcion="La salida íntegra del motor y el registro de la ventana")
    acciones.registrar("herr.web", "Abrir la versión &web", "internet-web-browser", None, "Herramientas", al_disparar=lambda *_: abrir_web(),
                       descripcion="La ventana que muestra la web de Raphi (raphi --web)")
    acciones.registrar("herr.lanzador", "Instalar el acceso &directo", "application-x-executable", None, "Herramientas", al_disparar=lambda *_: instalar_lanzador(),
                       operacion="instalacion", consecuencias="Escribe el acceso directo de Raphi Studio en el menú de aplicaciones de tu usuario (~/.local/share/applications) y su icono.")
    acciones.registrar("herr.venv", "El &entorno del motor…", "python", None, "Herramientas", al_disparar=pedir("venv"),
                       descripcion="Con qué intérprete corre el motor y cómo crear el .venv (install.sh)")
    # --- Ayuda
    acciones.registrar("ayuda.manual", "&Manual de Raphi Studio", "help-contents", StandardKey.HelpContents, "Ayuda",
                       al_disparar=lambda *_: espacio.abrir(str(APP_DIR / "README.md")))
    acciones.registrar("ayuda.referencia", "&Referencia de las operaciones", "help-hint", None, "Ayuda",
                       al_disparar=lambda *_: espacio.abrir(str(REPO / "docs" / "referencia-operaciones.md")))

    acciones.definir_menus([
        ("&Archivo", ["archivo.anadir", "archivo.anadir_carpeta", "archivo.quitar", "archivo.vaciar", "|", "archivo.abrir", "archivo.mostrar", "archivo.terminal",
                      "archivo.copiar", "|", "app.salir"]),
        ("&Editar", ["editar.buscar"]),
        ("&Ver", ["ver.catalogo", "ver.herramienta", "ver.cola", "ver.atras", "|", ("&Área", ["ver.area"] + [f"ver.area.{a[0]}" for a in familias.AREAS]),
                  "ver.aceptan", "|", "ver.releer", "|", "ventana.pantalla_completa"]),
        ("&Herramienta", ["op.simular", "op.aplicar", "op.cancelar", "|", "herramienta.restablecer"]),
        ("&Cola", ["ver.cola", "|", "trabajos.repetir", "trabajos.herramienta", "trabajos.quitar", "trabajos.limpiar"]),
        ("H&erramientas", [f"op.{o.id}" for o in ops.OPERACIONES if o.id != "herramienta"] + ["herr.salida", "|", "herr.faltan", "herr.dolphin", "herr.vigilar",
                           "|", "herr.web", "herr.lanzador", "herr.venv", "|", "ventana.paleta"]),
        ("A&justes", ["app.ajustes"]),
        ("Ay&uda", ["ayuda.manual", "ayuda.referencia", "app.acerca"]),
    ])
    acciones.anadir_fuente(espacio.entradas_paleta)
    acciones.anadir_fuente(herramientas.entradas_paleta)
    acciones.anadir_fuente(trabajos.entradas_paleta)
    acciones.anadir_fuente(archivos.entradas_paleta)

    def instalar_lanzador() -> None:
        if not tareas.activa:
            tareas.proceso("Instalando el acceso directo", [sys.executable, "-m", "escritorio.studio", "--instalar-lanzador"], cwd=str(REPO),
                           entorno={"PYTHONPATH": str(REPO)})

    def abrir_web() -> None:
        subprocess.Popen([rutas.interprete_motor(), "-m", "escritorio", "--web"], cwd=str(REPO), env={**os.environ, "PYTHONPATH": str(REPO)})
        consola.registrar("info", "La ventana web de Raphi se abre aparte (raphi --web).")

    def recibir(rutas_: list[str]) -> None:
        archivos.recibir(rutas_)

    def al_recibir(n: int) -> None:
        """Archivos que llegaron (soltados, Dolphin, otra instancia): con una herramienta abierta que los acepta, se
        quedan ahí; si no, el catálogo con lo que los acepta (y, si es una sola, esa herramienta)."""
        if not n:
            return
        if espacio.vista == "herramienta" and herramientas.hayActual and herramientas.aceptaLosArchivos:
            return
        if ajustes.filtrarAlRecibir:
            espacio.fijarSoloAceptan(True)
            que = herramientas.queAceptan()
            if len(que) == 1:
                herramientas.irA(que[0])
            else:
                espacio.fijarVista("catalogo")
                if not que:
                    interfaz.pedir.emit("aviso", {"texto": "Ninguna herramienta acepta esas entradas juntas.", "tipo": "aviso"})

    def vista_cambiada():
        for n, *_r in espacio_mod.VISTAS:
            acciones.marcar(f"ver.{n}", espacio.vista == n)
        disponibilidad()

    def filtro_cambiado():
        acciones.marcar("ver.area", espacio.area == "")
        for id_, *_r in familias.AREAS:
            acciones.marcar(f"ver.area.{id_}", espacio.area == id_)
        acciones.marcar("ver.aceptan", espacio.soloAceptan)
        disponibilidad()

    def disponibilidad():
        activa = tareas.activa
        hay_objetivo = bool(objetivo())
        for nombre in ("archivo.abrir", "archivo.mostrar", "archivo.terminal", "archivo.copiar"):
            acciones.habilitar(nombre, hay_objetivo)
        acciones.habilitar("archivo.quitar", archivos.total > 0)
        acciones.habilitar("archivo.vaciar", archivos.total > 0)
        acciones.habilitar("ver.herramienta", herramientas.hayActual)
        acciones.habilitar("herramienta.restablecer", herramientas.hayActual and bool(herramientas.valores))
        acciones.habilitar("op.simular", operaciones.puedeSimular and operaciones.actual == "herramienta")
        acciones.accion("op.aplicar").visible = operaciones.escribe or operaciones.actual == "herramienta"
        acciones.habilitar("op.aplicar", operaciones.puedeAplicar)
        acciones.habilitar("op.cancelar", operaciones.enCurso)
        acciones.habilitar("trabajos.repetir", trabajos.hayActual and trabajos.estado not in ("en_cola", "en_curso"))
        acciones.habilitar("trabajos.quitar", trabajos.hayActual and trabajos.estado == "en_cola")
        acciones.habilitar("trabajos.herramienta", trabajos.hayActual and trabajos.ref in herramientas.refs)
        acciones.habilitar("ver.releer", not activa)
        acciones.habilitar("herr.lanzador", not activa)

    def barra_estado():
        espacio.fijarResumen(f"{herramientas.resumen} · {trabajos.resumen}")
        partes = []
        if herramientas.hayActual:
            partes.append(f"{herramientas.titulo} · {archivos.resumen}")
        if trabajos.enCurso:
            partes.append(trabajos.textoEnCurso)
        espacio.fijarContexto(" · ".join(partes))

    archivos.recibidos.connect(al_recibir)
    herramientas.actualCambiado.connect(lambda: herramientas.hayActual and trabajos.irAlUltimoDe(herramientas.ref))
    herramientas.actualCambiado.connect(lambda: herramientas.hayActual and operaciones.fijar("herramienta"))   # elegir una herramienta es querer correrla
    espacio.vistaCambiada.connect(vista_cambiada)
    espacio.filtroCambiado.connect(filtro_cambiado)
    archivos.cambiado.connect(lambda: (disponibilidad(), barra_estado()))
    herramientas.cambiado.connect(lambda: (disponibilidad(), barra_estado()))
    herramientas.actualCambiado.connect(lambda: (disponibilidad(), barra_estado()))
    herramientas.opcionesCambiadas.connect(disponibilidad)
    trabajos.cambiado.connect(lambda: (disponibilidad(), barra_estado()))
    trabajos.actualCambiado.connect(disponibilidad)
    operaciones.cambiado.connect(lambda: (disponibilidad(), barra_estado()))
    vista.cambiado.connect(disponibilidad)
    tareas.cambiada.connect(disponibilidad)
    vista_cambiada()
    filtro_cambiado()
    barra_estado()

    piezas = dict(consola=consola, tareas=tareas, interfaz=interfaz, ajustes=ajustes, espacio=espacio, archivos=archivos, herramientas=herramientas,
                  trabajos=trabajos, operaciones=operaciones, vista=vista, acciones=acciones, recibir=recibir)
    for nombre, objeto in piezas.items():
        if nombre != "recibir":
            app.exponer(nombre, objeto)
    app.exponer("descripcionStudio", DESCRIPCION)
    app._piezas = piezas
    if releer and not herramientas.total:
        herramientas.releer_ahora()
    elif releer:
        herramientas.releer()
    return piezas


def vigilancia_para(piezas: dict):
    """Las carpetas vigiladas de siempre (`escritorio/vigilancia.py`) con el «servidor» resuelto por la cola del studio."""
    from gui_comun.qt import QSettings
    from escritorio.vigilancia import Vigilancia

    class Motor:
        def pedir(self, ruta: str, datos: dict | None = None):
            datos = datos or {}
            if ruta == "/api/raphi/locales":
                return [{"id": r} for r in datos.get("rutas", [])]
            if ruta == "/api/raphi/trabajos":
                receta = datos["operacion"].removeprefix("receta:")
                titulo = next((f["titulo"] for f in piezas["herramientas"]._fichas.values() if f.get("es_receta") and f["id"] == receta), receta)
                piezas["trabajos"].encolar(f"receta:{receta}", f"Carpeta vigilada: {titulo}", list(datos.get("archivos", [])), {}, datos.get("destino") or "", False)
                return {"ok": True}
            raise ValueError(f"Raphi Studio no atiende {ruta}")

    def avisar(titulo: str, texto: str) -> None:
        piezas["interfaz"].pedir.emit("aviso", {"texto": f"{titulo}: {texto}", "tipo": "informacion"})

    v = Vigilancia(Motor(), QSettings(), avisar)
    piezas["operaciones"].fijar_vigilancia(v)
    return v


def main(argv: list[str]) -> int:
    from gui_comun import lanzador
    atendido = lanzador.desde_main(argv, **datos_lanzador())
    if atendido is not None:
        return atendido
    humo = "--smoke" in argv
    rutas_ = [str(Path(a).resolve()) for a in argv if not a.startswith("-")]
    from gui_comun.qt import BINDING
    if BINDING == "PySide6":
        from PySide6.QtNetwork import QLocalServer, QLocalSocket
    else:
        from PyQt6.QtNetwork import QLocalServer, QLocalSocket
    if not humo:
        otro = QLocalSocket()
        otro.connectToServer(NOMBRE_SOCKET)
        if otro.waitForConnected(300):                      # ya hay una ventana (esta o la web): le mandamos los archivos
            otro.write(json.dumps(rutas_).encode())
            otro.waitForBytesWritten(1000)
            otro.disconnectFromServer()
            return 0
    if not rutas.hay_venv() and not os.environ.get(rutas.VARIABLE_MOTOR):
        print(f"{NOMBRE}: sin el entorno del motor las herramientas que necesitan pikepdf, PyMuPDF o Pillow fallarán. Créalo con:\n  {rutas.orden_crear_venv()}", file=sys.stderr)
    app = Aplicacion(APP_ID, NOMBRE, version=_version(), organizacion=ORG_NAME, nombre_ajustes=APP_NAME)
    piezas = construir(app)
    piezas["vigilancia"] = vigilancia_para(piezas)
    escucha = None
    if not humo:
        QLocalServer.removeServer(NOMBRE_SOCKET)
        escucha = QLocalServer()
        escucha.listen(NOMBRE_SOCKET)

        def llegada():
            conexion = escucha.nextPendingConnection()
            conexion.waitForReadyRead(1000)
            try:
                piezas["recibir"](json.loads(bytes(conexion.readAll()).decode() or "[]"))
            except ValueError:
                piezas["recibir"]([])
            piezas["interfaz"].pedir.emit("activar", {})

        escucha.newConnection.connect(llegada)
        app._escucha = escucha
    if rutas_:
        piezas["recibir"](rutas_)
    try:
        return app.ejecutar(QML_DIR / "Main.qml", humo=humo)
    finally:
        piezas["vista"].apagar()


def _version() -> str:
    try:
        from raphi import VERSION
        return VERSION
    except Exception:       # noqa: BLE001
        return "2.0.0"
