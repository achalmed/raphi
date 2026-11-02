#!/usr/bin/python3
"""escritorio/studio/capturar.py — una captura de Raphi Studio para la documentación sobre los ARCHIVOS DE MUESTRA
(`muestra.py`: un PDF, un PNG, unos subtítulos, un Markdown y una carpeta de juguete, nunca los del usuario) creados en
una carpeta temporal fuera de la carpeta de inicio, con HOME, configuración, caché y datos temporales (ninguna ruta de
la máquina en pantalla), el esquema de color que se pida, la vista (catálogo, herramienta o cola), el área, la búsqueda,
la herramienta, las entradas y, si se pide, la paleta de órdenes.

    /usr/bin/python3 escritorio/studio/capturar.py docs/figuras/raphi-studio-catalogo.png --esquema …/LliphiOscuro.colors --vista catalogo
    /usr/bin/python3 escritorio/studio/capturar.py docs/figuras/raphi-studio-herramienta.png --esquema …/LliphiOscuro.colors --vista herramienta --herramienta rotar --aplicar
    /usr/bin/python3 escritorio/studio/capturar.py docs/figuras/raphi-studio-cola.png --esquema …/LliphiClaro.colors --vista cola --aplicar
    /usr/bin/python3 escritorio/studio/capturar.py salida.png --paleta "pdf"

Antes de capturar corre de verdad, sobre la muestra, la herramienta elegida con el corredor del motor (el `.venv` del
repo): simulada (F5) y, con `--aplicar`, aplicada; la salida del panel inferior es la del motor. Corre con el Python
del sistema; el motor, con el `.venv` (`RAPHI_MOTOR_PYTHON` o `<repo>/.venv/bin/python`).
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    parser = argparse.ArgumentParser(description="Captura de Raphi Studio sobre los archivos de muestra")
    parser.add_argument("salida")
    parser.add_argument("--esquema", help="archivo .colors de KDE (relanza con XDG_CONFIG_HOME temporal)")
    parser.add_argument("--vista", default="catalogo", help="catalogo · herramienta · cola")
    parser.add_argument("--area", default="", help="el área del catálogo (vacío: todas)")
    parser.add_argument("--busqueda", default="", help="el texto de la búsqueda del catálogo")
    parser.add_argument("--sin-entradas-en-catalogo", action="store_true", help="en el catálogo, sin el aviso de las entradas")
    parser.add_argument("--herramienta", default="", help="la herramienta elegida (id de la operación; vacío: la primera que acepte los archivos)")
    parser.add_argument("--archivos", default="pdf,otro", help="qué archivos de la muestra son entradas (pdf, otro, png, srt, md, txt, wav, carpeta)")
    parser.add_argument("--aplicar", action="store_true", help="aplica de verdad la herramienta (además de simularla) antes de capturar")
    parser.add_argument("--sin-correr", action="store_true", help="no corre nada antes de capturar")
    parser.add_argument("--paleta", default=None, help="abre la paleta de órdenes con este texto")
    parser.add_argument("--ancho", type=int, default=1440)
    parser.add_argument("--alto", type=int, default=900)
    args = parser.parse_args()

    if "RAPHI_STUDIO_CAPTURA" not in os.environ:      # primera pasada: la muestra, el entorno temporal (y esquema), y relanzar
        from escritorio.studio import hay_gui_comun
        if not hay_gui_comun():
            print("capturar.py: falta gui_comun (pip, o GUI_COMUN_DIR)", file=sys.stderr)
            return 2
        from gui_comun.galeria.esquema import entorno_con_esquema
        from escritorio.studio import muestra
        carpeta = Path(tempfile.mkdtemp(prefix="raphi-studio-captura-", dir="/tmp"))   # fuera de la carpeta de inicio
        m = muestra.crear(carpeta / "muestra")
        hogar = Path(m.entorno["HOME"])
        config_usuario = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
        for nombre in ("kdeglobals", "kcminputrc", "Kvantum", "fontconfig"):
            origen = config_usuario / nombre
            if origen.is_dir():
                shutil.copytree(origen, hogar / ".config" / nombre, dirs_exist_ok=True)
            elif origen.is_file():
                shutil.copy2(origen, hogar / ".config" / nombre)
        env = entorno_con_esquema(Path(args.esquema).expanduser(), hogar / ".config") if args.esquema else dict(os.environ, XDG_CONFIG_HOME=str(hogar / ".config"))
        env.update(m.entorno)
        env.update({"XDG_DATA_HOME": str(Path.home() / ".local" / "share"), "RAPHI_STUDIO_CAPTURA": str(carpeta), "QT_QPA_PLATFORM": "offscreen",
                    "RAPHI_STUDIO_MUESTRA": str(m.raiz), "PYTHONPATH": str(REPO)})
        env.setdefault("QT_QPA_PLATFORMTHEME", "kde")
        if "GUI_COMUN_DIR" not in env:
            import gui_comun
            env["GUI_COMUN_DIR"] = str(Path(gui_comun.__file__).resolve().parents[1])
        orden = [sys.executable, str(AQUI / "capturar.py")] + [a for a in sys.argv[1:] if not a.startswith("--esquema") and a != args.esquema]
        codigo = subprocess.run(orden, env=env).returncode
        shutil.rmtree(carpeta, ignore_errors=True)
        return codigo

    from escritorio.studio import aplicacion, muestra
    from gui_comun.nucleo import Aplicacion
    from gui_comun.qt import QTimer

    m = muestra.crear(Path(os.environ["RAPHI_STUDIO_MUESTRA"]))
    app = Aplicacion(aplicacion.APP_ID, aplicacion.NOMBRE, version=aplicacion._version(), organizacion=aplicacion.ORG_NAME, nombre_ajustes=aplicacion.APP_NAME)
    piezas = aplicacion.construir(app)
    espacio, herramientas, archivos, trabajos, operaciones, interfaz = (piezas[k] for k in ("espacio", "herramientas", "archivos", "trabajos", "operaciones", "interfaz"))
    if not app.cargar(aplicacion.QML_DIR / "Main.qml"):
        return 1
    raiz = app.motor.rootObjects()[0]
    raiz.setProperty("width", args.ancho)
    raiz.setProperty("height", args.alto)
    pendientes = []

    def correr_siguiente():
        if piezas["tareas"].activa or trabajos.enCurso:
            QTimer.singleShot(150, correr_siguiente)
            return
        if pendientes:
            aplicar = pendientes.pop(0)
            if aplicar:
                operaciones.aplicar()
            else:
                operaciones.simular()
            QTimer.singleShot(150, correr_siguiente)
            return
        QTimer.singleShot(300, listo)

    def empezar():
        archivos.agregar([str(m.archivos[k]) for k in args.archivos.split(",") if k in m.archivos])
        ref = args.herramienta or (next(iter(herramientas.queAceptan()), "") if args.vista != "catalogo" else "")
        if ref:
            herramientas.irA(ref)
            operaciones.fijar("herramienta")
            if not args.sin_correr:
                pendientes.append(False)
                if args.aplicar:
                    pendientes.append(True)
        correr_siguiente()

    def listo():
        if args.vista == "catalogo" and args.sin_entradas_en_catalogo:
            archivos.vaciar()
        espacio.fijarArea(args.area)
        espacio.fijarBusqueda(args.busqueda)
        espacio.fijarVista(args.vista)
        if args.vista == "cola" and trabajos.id:
            trabajos.irA(trabajos.id)
            if trabajos.salidas:
                piezas["vista"].mostrar(trabajos.salidas[0])
        if args.paleta is not None:
            QTimer.singleShot(900, lambda: interfaz.pedir.emit("paleta", {"texto": args.paleta}))
        app.capturar(args.salida, espera_ms=3000)

    QTimer.singleShot(600, empezar)
    codigo = app.app.exec()
    piezas["vista"].apagar()
    app.cerrar()
    print("CAPTURA", args.salida)
    return codigo


if __name__ == "__main__":
    sys.exit(main())
