"""escritorio/studio/aplicacion.py — arma Raphi Studio: la aplicación (gui_comun.nucleo), los controladores, el registro
de acciones (menú, barra, menú contextual, paleta, atajos), la instancia única (los archivos que llegan de Dolphin o
de otra instancia van a la ventana abierta) y carga `qml/Main.qml`.

Toda operación existe una sola vez, aquí, en `Acciones`: F5 simula (la herramienta sobre los archivos como trabajo
simulado del corredor, o la CLI de solo lectura del motor) y Ctrl+Intro aplica tras confirmar en QML. Lo que necesita
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
from escritorio.studio.controladores.espacio import Espacio  # noqa: E402
from escritorio.studio.controladores.herramientas import Herramientas  # noqa: E402
from escritorio.studio.controladores.operaciones import Operaciones  # noqa: E402
from escritorio.studio.controladores.trabajos import Trabajos  # noqa: E402
from escritorio.studio.servicios import operaciones as ops  # noqa: E402
from escritorio.studio.servicios import rutas  # noqa: E402

APP_DIR = Path(__file__).resolve().parent
QML_DIR = APP_DIR / "qml"
RECURSOS_DIR = APP_DIR / "recursos"
REPO = rutas.REPO
APP_ID = "raphi"
NOMBRE = APP_NAME
NOMBRE_SOCKET = "raphi-escritorio"          # el mismo que la ventana web: Dolphin y la CLI no saben cuál está abierta
DESCRIPCION = ("Documentos, PDF, imágenes, audio y video en tu máquina, en una ventana de trabajo: las herramientas del motor de Raphi por familia "
               "con lo que les falta, los archivos que sueltas o eliges, las opciones de cada herramienta generadas de su ficha, y los trabajos con su "
               "cola, su progreso, su resultado y su registro. F5 simula (el plan: qué se producirá y dónde) y Ctrl+Intro aplica tras confirmar; el "
               "original nunca se toca. El motor corre como proceso con el entorno del repo; la misma herramienta está en la CLI (raphi), en la web y en Qillqa.")
ACENTO = "violeta"


def datos_lanzador() -> dict:
    return dict(app_id=APP_ID, nombre=NOMBRE, comentario="Documentos, PDF, imágenes, audio y video", orden=[str(REPO / "run.sh")],
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
    espacio = Espacio(consola, ajustes)
    archivos = Archivos(consola)
    herramientas = Herramientas(espacio, archivos, consola, tareas, cache=cache)
    trabajos = Trabajos(espacio, herramientas, consola, tareas, cache=cache)
    operaciones = Operaciones(espacio, herramientas, archivos, trabajos, consola, tareas, cache=cache)
    acciones = Acciones()
    acciones.estandar(NOMBRE)
    pedir = lambda que, **datos: (lambda *_: interfaz.pedir.emit(que, datos))

    def objetivo() -> str:
        if espacio.vista == "trabajos":
            return trabajos.salidaActual or (trabajos.archivos[0] if trabajos.archivos else "")
        return archivos.rutaActual or (archivos.rutas[0] if archivos.rutas else "")

    # --- Archivo
    acciones.registrar("archivo.anadir", "&Añadir archivos…", "document-open", StandardKey.Open, "Archivo", al_disparar=pedir("elegir_archivos"),
                       descripcion="Archivos para la lista (también se sueltan sobre la ventana)")
    acciones.registrar("archivo.anadir_carpeta", "Añadir una &carpeta…", "folder-open", "Ctrl+Shift+O", "Archivo", al_disparar=pedir("elegir_carpeta"),
                       descripcion="Una carpeta entera como entrada (las herramientas que trabajan con carpetas)")
    acciones.registrar("archivo.quitar", "&Quitar de la lista", "list-remove", "Delete", "Archivo", habilitada=False, al_disparar=pedir("quitar_archivos"))
    acciones.registrar("archivo.vaciar", "&Vaciar la lista", "edit-clear-list", None, "Archivo", habilitada=False, al_disparar=lambda *_: archivos.vaciar())
    acciones.registrar("archivo.abrir", "A&brir", "document-open", None, "Archivo", habilitada=False, al_disparar=lambda *_: espacio.abrir(objetivo()),
                       descripcion="El archivo seleccionado (o la salida) con la aplicación del sistema")
    acciones.registrar("archivo.mostrar", "&Mostrar en la carpeta", "system-file-manager", "Ctrl+Shift+M", "Archivo", habilitada=False,
                       al_disparar=lambda *_: espacio.mostrarEnCarpeta(objetivo()), descripcion="Dolphin con el archivo seleccionado")
    acciones.registrar("archivo.terminal", "Abrir &terminal aquí", "utilities-terminal", "Shift+F4", "Archivo", habilitada=False,
                       al_disparar=lambda *_: espacio.abrirTerminal(objetivo()))
    acciones.registrar("archivo.copiar", "Copiar la &ruta", "edit-copy", "Ctrl+Shift+C", "Archivo", habilitada=False, al_disparar=lambda *_: espacio.copiar(objetivo()))
    # --- Editar
    acciones.registrar("editar.filtrar", "&Filtrar", "edit-find", StandardKey.Find, "Editar", al_disparar=pedir("filtrar"))
    acciones.registrar("editar.todo", "Seleccionar &todo", "edit-select-all", StandardKey.SelectAll, "Editar", al_disparar=pedir("seleccionar_todo"))
    # --- Ver
    acciones.registrar("ver.vista.herramientas", "&1 Herramientas", "application-x-executable", "Ctrl+1", "Ver › Vista", marcable=True,
                       al_disparar=lambda *_: espacio.fijarVista("herramientas"))
    acciones.registrar("ver.vista.trabajos", "&2 Trabajos", "view-task", "Ctrl+2", "Ver › Vista", marcable=True, al_disparar=lambda *_: espacio.fijarVista("trabajos"))
    acciones.registrar("ver.familia", "&Todas las familias", "application-x-executable", "Ctrl+0", "Ver › Familia", marcable=True, al_disparar=lambda *_: espacio.fijarFamilia(""))
    for i, (id_, nombre, _p, icono) in enumerate(familias.FAMILIAS, start=1):
        acciones.registrar(f"ver.familia.{id_}", f"&{nombre}", icono, None, "Ver › Familia", marcable=True, al_disparar=lambda *_, n=id_: espacio.fijarFamilia(n))
    acciones.registrar("ver.aceptan", "Solo las que &aceptan los archivos", "view-filter", "Ctrl+Shift+A", "Ver", marcable=True,
                       al_disparar=lambda *_: espacio.fijarSoloAceptan(acciones.accion("ver.aceptan").marcada),
                       descripcion="La tabla de herramientas se queda con las que sirven para los archivos de la lista")
    acciones.registrar("ver.releer", "&Releer las fichas", "view-refresh", "F6", "Ver", al_disparar=lambda *_: herramientas.releer(),
                       descripcion="Vuelve a pedir al motor sus operaciones, recetas y lo que falta en esta máquina")
    # --- Herramienta (la operación actual) y Trabajos
    for o in ops.OPERACIONES:
        acciones.registrar(f"op.{o.id}", o.titulo, o.icono, None, "Herramienta", al_disparar=lambda *_, i=o.id: operaciones.fijar(i), descripcion=o.descripcion)
    acciones.registrar("op.simular", "&Simular", "system-run", StandardKey.Refresh, "Herramienta", al_disparar=operaciones.simular,
                       descripcion="La herramienta sobre los archivos en simulación (el plan: qué se producirá y dónde), o la orden de solo lectura elegida")
    acciones.registrar("op.aplicar", "&Aplicar…", "dialog-ok-apply", "Ctrl+Return", "Herramienta", habilitada=False, al_disparar=pedir("aplicar"),
                       descripcion="Muestra la herramienta, los archivos, las opciones y la salida; si confirmas, corre de verdad")
    acciones.registrar("op.cancelar", "&Cancelar el trabajo", "process-stop", "Escape", "Herramienta", habilitada=False, al_disparar=operaciones.cancelar,
                       descripcion="Detiene el trabajo en curso (también el programa que esté corriendo)")
    acciones.registrar("herramienta.restablecer", "&Restablecer las opciones", "edit-undo", "Ctrl+Shift+R", "Herramienta", habilitada=False,
                       al_disparar=lambda *_: herramientas.restablecerOpciones(), descripcion="Vuelve a las opciones por omisión de la herramienta")
    for i, (nombre, texto) in enumerate((("resumen", "Ver el &resumen"), ("archivos", "Ver los &archivos"), ("opciones", "Ver las &opciones"),
                                         ("resultado", "Ver el r&esultado"))):
        acciones.registrar(f"herramienta.{nombre}", texto, "", None, "Herramienta", al_disparar=pedir("pestana", indice=i))
    acciones.registrar("trabajos.quitar", "&Quitar de la cola", "list-remove", None, "Trabajos", habilitada=False, al_disparar=lambda *_: trabajos.quitarDeLaCola(trabajos.id))
    acciones.registrar("trabajos.limpiar", "&Limpiar los terminados", "edit-clear-history", None, "Trabajos", al_disparar=lambda *_: trabajos.limpiarHechos(),
                       descripcion="Quita de la lista los trabajos hechos, fallidos y cancelados; las salidas no se tocan")
    acciones.registrar("trabajos.herramienta", "Ir a su &herramienta", "go-jump", None, "Trabajos", habilitada=False, al_disparar=lambda *_: herramientas.irA(trabajos.ref))
    # --- Herramientas
    acciones.registrar("herr.dolphin", "Menús de &Dolphin…", "system-file-manager", None, "Herramientas", al_disparar=pedir("dolphin"),
                       descripcion="Instalar o quitar «Raphi ▸ …» del clic derecho de Dolphin")
    acciones.registrar("herr.vigilar", "Carpetas &vigiladas…", "folder-sync", None, "Herramientas", al_disparar=pedir("vigilar"),
                       descripcion="Una carpeta cuyo contenido nuevo pasa por una receta")
    acciones.registrar("herr.faltan", "Lo que &falta en esta máquina…", "dialog-warning", None, "Herramientas", al_disparar=pedir("faltan"))
    acciones.registrar("herr.web", "Abrir la versión &web", "internet-web-browser", None, "Herramientas", al_disparar=lambda *_: abrir_web(),
                       descripcion="La ventana que muestra la web de Raphi (raphi --web)")
    acciones.registrar("herr.lanzador", "Instalar el acceso &directo", "application-x-executable", None, "Herramientas", al_disparar=lambda *_: instalar_lanzador())
    acciones.registrar("herr.venv", "El &entorno del motor…", "python", None, "Herramientas", al_disparar=pedir("venv"),
                       descripcion="Con qué intérprete corre el motor y cómo crear el .venv (install.sh)")
    # --- Ayuda
    acciones.registrar("ayuda.manual", "&Manual de Raphi Studio", "help-contents", StandardKey.HelpContents, "Ayuda",
                       al_disparar=lambda *_: subprocess.Popen(["xdg-open", str(APP_DIR / "README.md")]))
    acciones.registrar("ayuda.referencia", "&Referencia de las operaciones", "help-hint", None, "Ayuda",
                       al_disparar=lambda *_: subprocess.Popen(["xdg-open", str(REPO / "docs" / "referencia-operaciones.md")]))

    acciones.definir_menus([
        ("&Archivo", ["archivo.anadir", "archivo.anadir_carpeta", "archivo.quitar", "archivo.vaciar", "|", "archivo.abrir", "archivo.mostrar", "archivo.terminal",
                      "archivo.copiar", "|", "app.salir"]),
        ("&Editar", ["editar.filtrar", "editar.todo"]),
        ("&Ver", ["ventana.navegacion", "ventana.detalles", "ventana.inferior", "|", ("&Vista", ["ver.vista.herramientas", "ver.vista.trabajos"]),
                  ("&Familia", ["ver.familia"] + [f"ver.familia.{f[0]}" for f in familias.FAMILIAS]), "ver.aceptan", "|", "ver.releer", "|", "ventana.pantalla_completa"]),
        ("&Herramienta", ["op.simular", "op.aplicar", "op.cancelar", "|", "herramienta.restablecer", "|"] + [f"op.{o.id}" for o in ops.OPERACIONES]
                         + ["|", "herramienta.resumen", "herramienta.archivos", "herramienta.opciones", "herramienta.resultado"]),
        ("&Trabajos", ["ver.vista.trabajos", "|", "trabajos.herramienta", "trabajos.quitar", "trabajos.limpiar"]),
        ("H&erramientas", ["herr.dolphin", "herr.vigilar", "herr.faltan", "|", "herr.web", "herr.lanzador", "herr.venv", "|", "ventana.paleta"]),
        ("A&justes", ["app.ajustes"]),
        ("Ay&uda", ["ayuda.manual", "ayuda.referencia", "app.acerca"]),
    ])
    acciones.definir_barra(["op.simular", "op.aplicar", "|", "archivo.anadir", "archivo.anadir_carpeta"])
    acciones.anadir_fuente(espacio.entradas_paleta)
    acciones.anadir_fuente(operaciones.entradas_paleta)
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
        """Archivos que llegaron (soltados, Dolphin, otra instancia): si se quiere, la tabla con lo que los acepta."""
        if n and ajustes.filtrarAlRecibir:
            espacio.fijarVista("herramientas")
            espacio.fijarSoloAceptan(True)
            que = herramientas.queAceptan()
            if len(que) == 1:
                herramientas.irA(que[0])
            elif not que:
                interfaz.pedir.emit("aviso", {"texto": "Ninguna herramienta acepta esos archivos juntos.", "tipo": "aviso"})
        interfaz.pedir.emit("pestana", {"indice": 1})

    def vista_cambiada():
        acciones.marcar("ver.vista.herramientas", espacio.vista == "herramientas")
        acciones.marcar("ver.vista.trabajos", espacio.vista == "trabajos")
        disponibilidad()

    def filtro_cambiado():
        acciones.marcar("ver.familia", espacio.familia == "")
        for id_, *_r in familias.FAMILIAS:
            acciones.marcar(f"ver.familia.{id_}", espacio.familia == id_)
        acciones.marcar("ver.aceptan", espacio.soloAceptan)
        disponibilidad()

    def disponibilidad():
        activa = tareas.activa
        en_trabajos = espacio.vista == "trabajos"
        hay_objetivo = bool(objetivo())
        for nombre in ("archivo.abrir", "archivo.mostrar", "archivo.terminal", "archivo.copiar"):
            acciones.habilitar(nombre, hay_objetivo)
        acciones.habilitar("archivo.quitar", not en_trabajos and archivos.total > 0)
        acciones.habilitar("archivo.vaciar", archivos.total > 0)
        acciones.habilitar("herramienta.restablecer", herramientas.hayActual and bool(herramientas.valores))
        a = acciones.accion("op.simular")
        a.texto = f"&{operaciones.verbo}"
        acciones.habilitar("op.simular", operaciones.puedeSimular)
        b = acciones.accion("op.aplicar")
        b.visible = operaciones.escribe
        acciones.habilitar("op.aplicar", operaciones.puedeAplicar)
        acciones.habilitar("op.cancelar", operaciones.enCurso)
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
    herramientas.actualCambiado.connect(lambda: espacio.vista == "herramientas" and trabajos.irAlUltimoDe(herramientas.ref))
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
    tareas.cambiada.connect(disponibilidad)
    vista_cambiada()
    filtro_cambiado()
    barra_estado()

    piezas = dict(consola=consola, tareas=tareas, interfaz=interfaz, ajustes=ajustes, espacio=espacio, archivos=archivos, herramientas=herramientas,
                  trabajos=trabajos, operaciones=operaciones, acciones=acciones, recibir=recibir)
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
    return app.ejecutar(QML_DIR / "Main.qml", humo=humo)


def _version() -> str:
    try:
        from raphi import VERSION
        return VERSION
    except Exception:       # noqa: BLE001
        return "2.0.0"
