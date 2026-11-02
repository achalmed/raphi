"""tests/studio/test_ventana.py — Raphi Studio (reingeniería: QML + Kirigami sobre gui-comun 3.0, VentanaBase) abre su
ventana sin pantalla con el Python del sistema sobre los archivos de muestra: la ventana entera (acciones, menús, las
tres vistas, los archivos recibidos y la herramienta que los acepta, un trabajo simulado con el motor, la vista previa
de un PDF y de un audio), cada componente QML, `--smoke`, y las
reglas de la familia (sin colores propios, sin marca dentro, sin QtWidgets, ninguna operación nombrada fuera de
familias.py; ninguna prueba descarga ni transcribe ni toca los archivos del usuario)."""
from __future__ import annotations

import ast
import json
import re
import subprocess

import pytest

from conftest import MOTOR, PYTHON_SISTEMA, REPO, STUDIO, correr_python, entorno_gui, requiere_sistema

QML = STUDIO / "qml"

ABRIR = """
import sys, json, os, time; sys.path.insert(0, sys.argv[1])
from escritorio.studio import aplicacion, muestra
from gui_comun.nucleo import Aplicacion
from gui_comun.qt import QTimer
m = muestra.crear(os.environ["RAPHI_STUDIO_MUESTRA"])
app = Aplicacion("raphi", "Raphi Studio", version="prueba", organizacion="raphi-pruebas", nombre_ajustes="Raphi Studio pruebas")
piezas = aplicacion.construir(app)
errores = []
app.motor.warnings.connect(lambda avisos: errores.extend(a.toString() for a in avisos))
ok = app.cargar(aplicacion.QML_DIR / "Main.qml")
raiz = app.motor.rootObjects()[0] if ok else None
a, h, ar, t, o, e = piezas["acciones"], piezas["herramientas"], piezas["archivos"], piezas["trabajos"], piezas["operaciones"], piezas["espacio"]
sin = (a.accion("op.simular").habilitada, a.accion("op.aplicar").habilitada, a.accion("archivo.quitar").habilitada, e.vista)
n = ar.recibir([str(m.archivos["srt"])])
tras_recibir = (e.soloAceptan, h.modelo.filas, h.ref, e.vista)
h.irA("convertir_subtitulos")
con = (a.accion("op.simular").habilitada, a.accion("op.aplicar").habilitada, a.accion("op.simular").textoPlano, o.actual)
corrio = o.simular() if os.environ.get("RAPHI_MOTOR_PYTHON") else None
inicio = time.monotonic()
while (piezas["tareas"].activa or t.enCurso) and time.monotonic() - inicio < 120:
    app.app.processEvents(); time.sleep(0.05)
app.app.processEvents()
titulo = raiz.property("title") if raiz else ""
v = piezas["vista"]
v.mostrar(str(m.archivos["wav"])); audio = (v.tipo, v.url.endswith(".wav"))
v.mostrar(str(m.archivos["pdf"])); pdf = (v.tipo, v.paginas.filas)
e.fijarVista("cola"); en_cola = (e.vista, raiz.property("title"))
e.fijarVista("catalogo"); e.fijarArea("transcripcion"); catalogo = (e.vista, h.visibles)
confirma = (a.accion("op.aplicar").operacion, a.accion("op.aplicar").requiereConfirmacion)
QTimer.singleShot(800, app.app.quit); app.app.exec(); app.cerrar()
print(json.dumps({"ok": ok, "titulo": titulo, "errores": errores, "acciones": a.nombres(), "menus": [x["titulo"] for x in a.menus], "barra": a.barra, "sin": sin, "n": n,
                  "tras_recibir": tras_recibir, "con": con, "corrio": corrio, "estado": t.estado, "simulado": t.simulado, "resultado": t.resultado[:200],
                  "resumen": e.resumen, "contexto": e.contexto, "total": h.total, "audio": audio, "pdf": pdf, "en_cola": en_cola, "catalogo": catalogo,
                  "confirma": confirma, "clase": type(app.app).__name__}))
"""

COMPONENTE = """
import sys, json, os; sys.path.insert(0, sys.argv[1])
from escritorio.studio import aplicacion
from gui_comun.nucleo import Aplicacion
from gui_comun.qt import QTimer
app = Aplicacion("raphi", "Raphi Studio", version="prueba", organizacion="raphi-pruebas", nombre_ajustes="Raphi Studio pruebas")
aplicacion.construir(app, releer=False)
app.motor.addImportPath(str(aplicacion.QML_DIR))
errores = []
app.motor.warnings.connect(lambda avisos: errores.extend(a.toString() for a in avisos))
nombre, carpeta = sys.argv[2], sys.argv[3]
ruta = os.path.join(os.environ["XDG_CACHE_HOME"], "Prueba_" + nombre + ".qml")
os.makedirs(os.path.dirname(ruta), exist_ok=True)
open(ruta, "w").write('import QtQuick\\nimport GuiComun\\nimport "file://%s/%s"\\nVentanaStudio { id: ventana; acciones: studio.acciones; visible: false; %s { id: objeto } }\\n' % (str(aplicacion.QML_DIR), carpeta, nombre))
ok = app.cargar(ruta)
QTimer.singleShot(400, app.app.quit); app.app.exec(); app.cerrar()
print(json.dumps({"ok": ok, "errores": errores}))
"""


def _graves(errores):
    return [e for e in errores if "TypeError" in e or "ReferenceError" in e or "is not a type" in e or "Cannot assign" in e or "No se puede asignar" in e]


@requiere_sistema
def test_abre_y_cierra_su_ventana(tmp_path, muestra):
    r = correr_python(ABRIR, entorno_gui(tmp_path, muestra), plazo=300)
    assert r.returncode == 0, f"código {r.returncode}\n{r.stderr[-3000:]}"
    datos = json.loads(r.stdout.strip().splitlines()[-1])
    assert datos["ok"], r.stderr[-3000:]
    assert not _graves(datos["errores"]), "\n".join(_graves(datos["errores"]))
    for n in ("archivo.anadir", "archivo.anadir_carpeta", "archivo.quitar", "archivo.vaciar", "archivo.abrir", "archivo.mostrar", "archivo.terminal", "archivo.copiar",
              "editar.buscar", "ver.catalogo", "ver.herramienta", "ver.cola", "ver.atras", "ver.area", "ver.area.transcripcion", "ver.aceptan", "ver.releer",
              "op.doctor", "op.lista", "op.formatos", "op.simular", "op.aplicar", "op.cancelar", "herramienta.restablecer",
              "trabajos.repetir", "trabajos.quitar", "trabajos.limpiar", "trabajos.herramienta", "herr.dolphin", "herr.vigilar", "herr.faltan", "herr.salida",
              "herr.web", "herr.lanzador", "herr.venv", "ayuda.manual", "ayuda.referencia", "ventana.paleta", "app.ajustes", "app.acerca", "app.salir"):
        assert n in datos["acciones"], n
    assert datos["menus"] == ["&Archivo", "&Editar", "&Ver", "&Herramienta", "&Cola", "H&erramientas", "A&justes", "Ay&uda"]
    assert datos["clase"] == "QApplication"                                  # gui-comun 3.0: los diálogos de KDE
    assert datos["sin"] == [False, False, False, "catalogo"] and datos["n"] == 1
    assert datos["tras_recibir"][0] is True and datos["tras_recibir"][1] >= 1
    assert datos["con"] == [True, True, "Simular", "herramienta"]
    assert datos["confirma"] == ["escritura", True]                          # Procesar lo confirma la base
    assert datos["audio"] == ["audio", True] and datos["pdf"][0] == "pdf"
    assert datos["en_cola"][0] == "cola" and datos["en_cola"][1].startswith("Cola") and datos["catalogo"][0] == "catalogo" and datos["catalogo"][1] >= 1
    if MOTOR:
        assert datos["total"] >= 60 and datos["corrio"] and datos["estado"] == "hecho" and datos["simulado"] and "entrevista.vtt" in datos["resultado"]
        assert datos["resumen"].startswith(f"{datos['total']} herramientas · ") and "1 trabajos: 0 en cola · 0 en curso · 1 hechos" in datos["resumen"]
    assert datos["contexto"].startswith("Convertir subtítulos · 1 archivo: entrevista.srt") and datos["titulo"].startswith("Convertir subtítulos")


@requiere_sistema
def test_main_smoke(tmp_path, muestra):
    r = subprocess.run([PYTHON_SISTEMA, "-m", "escritorio.studio", "--smoke"], env=entorno_gui(tmp_path, muestra), capture_output=True, text=True, timeout=240, cwd=tmp_path)
    assert r.returncode == 0, f"código {r.returncode}\n{r.stderr[-3000:]}"
    ruido = [l for l in r.stderr.splitlines() if "TypeError" in l or "ReferenceError" in l or "polish() loop" in l]
    assert not ruido, "\n".join(ruido)


COMPONENTES = sorted((p.parent.name, p.stem) for p in QML.glob("*/*.qml"))


@requiere_sistema
@pytest.mark.parametrize("carpeta,nombre", COMPONENTES, ids=[f"{c}/{n}" for c, n in COMPONENTES])
def test_cada_componente_qml(carpeta, nombre, tmp_path, muestra):
    r = correr_python(COMPONENTE, entorno_gui(tmp_path, muestra), nombre, carpeta)
    assert r.returncode == 0, r.stderr[-3000:]
    datos = json.loads(r.stdout.strip().splitlines()[-1])
    assert datos["ok"], r.stderr[-3000:]
    assert not _graves(datos["errores"]), "\n".join(_graves(datos["errores"]))


def test_sin_colores_propios_en_qml():
    malos = []
    for qml in QML.rglob("*.qml"):
        for n, linea in enumerate(qml.read_text(encoding="utf-8").splitlines(), 1):
            sin_comentario = linea.split("//")[0]
            if re.search(r'"#[0-9a-fA-F]{3,8}"', sin_comentario) or re.search(r'\bfont\.(pointSize|pixelSize|family)\s*:\s*["\d]', sin_comentario):
                malos.append(f"{qml.relative_to(STUDIO)}:{n}: {linea.strip()}")
    assert not malos, "\n".join(malos)


def test_sin_marca_dentro_de_la_ventana():
    codigo = "\n".join(l.split("//")[0] for l in (QML / "Main.qml").read_text(encoding="utf-8").splitlines())
    assert "logotipo" not in codigo.lower() and "logo_svg" not in codigo and "marca.svg" not in codigo
    assert 'text: "Raphi Studio"' not in codigo and "Kirigami.Heading" not in codigo.split("centro:")[0]


def test_sin_qtwidgets_y_sin_subir_carpetas():
    for py in STUDIO.rglob("*.py"):
        texto = py.read_text(encoding="utf-8")
        assert "QtWidgets" not in texto and "gui_comun.widgets" not in texto and "gui_comun.diseno" not in texto, py
    init = (STUDIO / "__init__.py").read_text(encoding="utf-8")
    assert "GUI_COMUN_DIR" in init and "d.parent" not in init                       # instalado o por la variable, nunca subiendo carpetas
    run = (REPO / "run.sh").read_text(encoding="utf-8")
    assert "GUI_COMUN_DIR" in run
    assert "ninguna prueba descarga ni transcribe" in (REPO / "tests" / "studio" / "test_ventana.py").read_text(encoding="utf-8")


def test_ninguna_pantalla_a_mano():
    """Las pantallas salen de las fichas: ni el Python ni el QML del studio nombran operaciones, salvo el mapa de familias."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("base", REPO / "raphi" / "motor" / "base.py")
    ids = set()
    for archivo in (REPO / "raphi" / "motor").glob("*.py"):
        for nodo in ast.walk(ast.parse(archivo.read_text(encoding="utf-8"))):
            if isinstance(nodo, ast.Call) and getattr(nodo.func, "id", "") == "operacion" and nodo.args and isinstance(nodo.args[0], ast.Constant):
                ids.add(nodo.args[0].value)
    assert len(ids) >= 60
    ids -= {"info", "ok", "error", "aviso", "lista"}
    for archivo in STUDIO.rglob("*.py"):
        if archivo.name in ("familias.py",) or archivo.parent.name == "__pycache__":
            continue
        cadenas = {n.value for n in ast.walk(ast.parse(archivo.read_text(encoding="utf-8"))) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        assert not cadenas & ids, f"{archivo.relative_to(STUDIO)} nombra {sorted(cadenas & ids)}"
    for qml in QML.rglob("*.qml"):
        texto = "\n".join(l.split("//")[0] for l in qml.read_text(encoding="utf-8").splitlines())
        nombradas = {i for i in ids if re.search(rf'"{re.escape(i)}"', texto)}
        assert not nombradas, f"{qml.name} nombra {sorted(nombradas)}"
