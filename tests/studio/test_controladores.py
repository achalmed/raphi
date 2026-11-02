"""tests/studio/test_controladores.py — los controladores de la ventana en proceso (sin QML) sobre los archivos de muestra:
espacio (vistas y filtros), archivos (la lista), herramientas (el catálogo desde las fichas, los filtros por área, por la
búsqueda y por
los archivos que aceptan, la actual con sus campos y sus opciones recordadas, la salida), trabajos y operaciones (F5
simula como trabajo, Ctrl+Intro aplica, la cola, el resultado con su vista previa, la CLI de solo lectura). Con el
.venv del repo corre el motor de verdad (convertir subtítulos y rotar un PDF); nada descarga ni transcribe."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from conftest import MOTOR, requiere_binding, requiere_motor

from test_servicios import FICHAS_MINIMAS


def _esperar(app, tareas, trabajos=None, segundos=240):
    inicio = time.monotonic()
    while (tareas.activa or (trabajos is not None and trabajos.enCurso)) and time.monotonic() - inicio < segundos:
        app.processEvents()
        time.sleep(0.05)
    app.processEvents()


@pytest.fixture
def piezas(app, muestra, ajustes_temporales):
    from gui_comun.consola import Consola
    from gui_comun.tareas import Tareas
    from escritorio.studio.controladores.ajustes import Ajustes
    from escritorio.studio.controladores.archivos import Archivos
    from escritorio.studio.controladores.espacio import Espacio
    from escritorio.studio.controladores.herramientas import Herramientas
    from escritorio.studio.controladores.operaciones import Operaciones
    from escritorio.studio.controladores.trabajos import Trabajos
    from escritorio.studio.servicios import fichas as svc_fichas
    cache = ajustes_temporales / "cache" / "studio"
    consola = Consola()
    tareas = Tareas(consola)
    ajustes = Ajustes()
    espacio = Espacio(consola, ajustes)
    archivos = Archivos(consola)
    herramientas = Herramientas(espacio, archivos, consola, tareas, cache=cache)
    if MOTOR:
        assert herramientas.releer_ahora()
    else:
        svc_fichas.guardar_cache(cache / "fichas.json", FICHAS_MINIMAS)
        assert herramientas.cargar_cache()
    trabajos = Trabajos(espacio, herramientas, consola, tareas, cache=cache)
    operaciones = Operaciones(espacio, herramientas, archivos, trabajos, consola, tareas, cache=cache)
    herramientas.actualCambiado.connect(lambda: herramientas.hayActual and operaciones.fijar("herramienta"))
    yield dict(consola=consola, tareas=tareas, espacio=espacio, archivos=archivos, herramientas=herramientas, trabajos=trabajos, operaciones=operaciones,
               ajustes=ajustes, muestra=muestra, cache=cache)
    _esperar(app, tareas, trabajos, 10)


@requiere_binding
def test_espacio_y_archivos(piezas):
    e, a, m = piezas["espacio"], piezas["archivos"], piezas["muestra"]
    assert e.vista == "catalogo" and e.area == "" and e.textoArea == "Todas las herramientas"
    e.fijarArea("audio")
    assert e.area == "audio" and e.textoArea == "Audio" and e.vista == "catalogo"
    e.fijarVista("cola")
    e.fijarGrupo("hechos")
    assert e.vista == "cola" and e.grupo == "hechos" and e.textoGrupo == "Hechos"
    e.fijarBusqueda("vídeo")
    assert e.vista == "catalogo" and e.busqueda == "vídeo" and "«vídeo»" in e.textoFiltro
    e.fijarArea("no-existe")
    assert e.area == ""
    assert a.total == 0 and a.resumen == "sin archivos"
    assert a.agregar([str(m.archivos["pdf"]), str(m.archivos["pdf"]), "/no/existe.pdf", m.archivos["otro"].as_uri()]) == 2
    assert a.total == 2 and a.rutas == [str(m.archivos["pdf"]), str(m.archivos["otro"])] and a.resumen.startswith("2 archivos: oficio.pdf, anexo.pdf")
    assert a.modelo.fila(0)["tipo"] == "PDF" and a.carpetaComun == str(m.archivos["pdf"].parent)
    a.quitar(0)
    assert a.rutas == [str(m.archivos["otro"])]
    a.vaciar()
    assert a.total == 0


def _refs_visibles(h) -> list:
    return [h.modelo.sourceModel().fila(h.modelo.filaOrigen(i))["ref"] for i in range(h.modelo.filas)]


@requiere_binding
def test_herramientas_catalogo_filtros_y_actual(piezas):
    h, e, a, m = piezas["herramientas"], piezas["espacio"], piezas["archivos"], piezas["muestra"]
    assert h.total >= 4 and h.listas >= 2 and h.porArea[""] == h.total and h.visibles == h.total
    assert "pdf" in {f["familia"] for f in (h.ficha(r) for r in h.refs)} and any(h.ficha(r)["es_receta"] for r in h.refs)
    fila = h.modelo.sourceModel().fila(0)
    assert {"titulo", "descripcion", "icono", "areaTexto", "formatos", "disponible", "estado"} <= set(fila)
    e.fijarArea("recetas")
    assert h.modelo.filas >= 1 and all(h.ficha(r)["es_receta"] for r in _refs_visibles(h))
    e.fijarArea("transcripcion")
    assert "convertir_subtitulos" in _refs_visibles(h)
    e.fijarArea("")
    e.fijarBusqueda("subtitulos")                      # sin tilde encuentra «subtítulos»
    assert "convertir_subtitulos" in _refs_visibles(h) and "unir" not in _refs_visibles(h)
    e.fijarBusqueda("")
    a.agregar([str(m.archivos["srt"])])
    e.fijarSoloAceptan(True)
    aceptan = h.queAceptan()
    assert "convertir_subtitulos" in aceptan and "unir" not in aceptan and h.modelo.filas == len(aceptan)
    assert h.irA("convertir_subtitulos") and h.hayActual and h.titulo == "Convertir subtítulos" and h.familia == "audio_video" and h.aceptaLosArchivos
    assert e.vista == "herramienta" and h.textoAreas.startswith("Transcripción") and h.formatos == "SRT VTT"
    assert h.campos == [] and h.resumenMarkdown.startswith("# Convertir subtítulos")
    assert h.irA("unir") and e.vista == "herramienta"
    assert [c["clave"] for c in h.campos][:1] == ["nombre"] and h.valores == {} and h.minimoEntradas == 2 and not h.aceptaLosArchivos
    h.fijarValor("nombre", "paquete")
    assert h.valores == {"nombre": "paquete"} and h.textoOpciones == "nombre = paquete"
    h.irA("convertir_subtitulos")
    h.irA("unir")
    assert h.valores == {"nombre": "paquete"}                                   # se recuerdan por herramienta
    h.restablecerOpciones()
    assert h.valores == {}
    assert h.destinoEfectivo == "junto a cada original"
    h.fijarDestino(str(m.raiz))
    assert h.enCarpeta and h.destinoEfectivo == str(m.raiz)
    h.fijarEnCarpeta(False)
    assert h.destinoEfectivo == "junto a cada original"
    nombres = [x["texto"] for x in h.entradas_paleta("")]
    assert "Unir PDF" in nombres


@requiere_binding
def test_operaciones_sin_poder(piezas):
    o, h, a, m = piezas["operaciones"], piezas["herramientas"], piezas["archivos"], piezas["muestra"]
    assert o.actual == "herramienta" and not o.puedeSimular and o.motivoNoSimular == "Elige primero una herramienta en el catálogo."
    h.irA("unir")
    assert "necesita al menos 2" in o.motivoNoSimular
    a.agregar([str(m.archivos["pdf"]), str(m.archivos["srt"])])
    assert "acepta PDF" in o.motivoNoSimular
    a.vaciar()
    a.agregar([str(m.archivos["pdf"]), str(m.archivos["otro"])])
    assert o.puedeSimular and o.puedeAplicar and o.escribe and o.verbo == "Simular"
    assert o.ordenSimular.startswith("operación unir · 2 archivo(s)") and "simulada" in o.ordenSimular and "de verdad" in o.ordenAplicar
    assert "Herramienta: Unir PDF" in o.textoConfirmacion and "Archivos: 2 archivos" in o.textoConfirmacion
    h.fijarEnCarpeta(True)
    h.fijarDestino("")
    assert "Elige la carpeta de salida" in o.motivoNoSimular
    o.fijar("doctor")
    assert o.puedeSimular and not o.escribe and o.verbo == "Ejecutar" and o.motivoNoAplicar.startswith("Esta operación no tiene modo")
    o.fijar("formatos")
    assert o.puedeSimular and o.ordenSimular.endswith("anexo.pdf")


@requiere_binding
@requiere_motor
def test_trabajos_simular_aplicar_y_la_cli(piezas, app):
    o, h, a, t, tr, m = piezas["operaciones"], piezas["herramientas"], piezas["archivos"], piezas["trabajos"], piezas["tareas"], piezas["muestra"]
    a.agregar([str(m.archivos["srt"])])
    assert h.irA("convertir_subtitulos") and o.actual == "herramienta" and o.puedeSimular
    terminados = []
    t.terminado.connect(lambda i, s, e: terminados.append((i, s, e)))
    assert o.simular()
    _esperar(app, tr, t)
    assert terminados and terminados[0][1] is True and terminados[0][2] == "hecho"
    assert t.hayActual and t.simulado and t.estado == "hecho" and "entrevista.srt → entrevista.vtt" in t.resultado and t.nSalidas == 0
    assert t.contadores == {"todos": 1, "en_cola": 0, "en_curso": 0, "hechos": 1, "con_error": 0} and t.resumen.startswith("1 trabajos: 0 en cola")
    assert o.aplicar()
    _esperar(app, tr, t)
    assert t.estado == "hecho" and not t.simulado and t.nSalidas == 1 and t.salidas[0].endswith("entrevista.vtt") and t.vistaPrevia == "texto" and "WEBVTT" in t.textoSalida
    assert t.registro.startswith("✓ ") and t.salidasModelo.fila(0)["nombre"] == "entrevista.vtt" and t.duracion.endswith("s")
    assert m.archivos["srt"].read_text(encoding="utf-8").startswith("1\n")                       # el original no se toca
    assert (m.archivos["srt"].parent / "entrevista.vtt").is_file()
    assert t.ultimoDe("convertir_subtitulos")["estado"] == "hecho" and t.filaDe(t.id) >= 0
    # un PDF rotado a otra carpeta, dos en cola: uno tras otro
    a.vaciar()
    a.agregar([str(m.archivos["pdf"])])
    assert h.irA("rotar")
    h.fijarValor("angulo", "180")
    h.fijarDestino(str(m.raiz / "salida"))
    assert o.aplicar() and o.aplicar()
    assert t.contadores["en_curso"] + t.contadores["en_cola"] == 2
    _esperar(app, tr, t)
    assert t.contadores == {"todos": 4, "en_cola": 0, "en_curso": 0, "hechos": 4, "con_error": 0}
    assert [f["seccion"] for f in t.modelo.sourceModel().todas()] == ["Hechos"] * 4             # la cola por secciones
    assert sorted(p.name for p in (m.raiz / "salida").iterdir()) == ["oficio_rotado-2.pdf", "oficio_rotado.pdf"]
    assert m.archivos["pdf"].stat().st_size > 0
    # repetir: el mismo trabajo (entradas, opciones, salida) otra vez a la cola, sin pisar lo anterior
    rotado = t.id
    nuevo = t.repetir(rotado)
    assert nuevo and nuevo != rotado
    _esperar(app, tr, t)
    assert t.contadores["hechos"] == 5 and "oficio_rotado-3.pdf" in {p.name for p in (m.raiz / "salida").iterdir()}
    # un trabajo que falla por archivo (un PDF que no es PDF): con error, con su mensaje
    malo = m.raiz / "malo.pdf"
    malo.write_text("esto no es un PDF", encoding="utf-8")
    a.vaciar()
    a.agregar([str(malo)])
    assert o.aplicar()
    _esperar(app, tr, t)
    assert t.estado == "fallido" and t.contadores["con_error"] == 1 and "malo.pdf" in t.resultado
    malo.unlink()
    avisos = []
    t.aviso.connect(lambda texto, tipo: avisos.append(texto))
    assert t.repetir(t.id) == "" and "ya no existe malo.pdf" in avisos[-1]      # sin su entrada, no se repite
    # la CLI de solo lectura
    o.fijar("doctor")
    assert o.simular()
    _esperar(app, tr, t)
    assert "operaciones disponibles" in o.salida
    t.limpiarHechos()
    assert t.total == 0 and not t.hayActual


@requiere_binding
def test_lista_de_trabajos_persistida(piezas, muestra):
    t, c = piezas["trabajos"], piezas["cache"]
    ident = t.encolar("receta:para-enviar", "Para enviar", [str(muestra.archivos["pdf"])], {}, "", True)
    assert t.hayActual and t.id == ident
    from escritorio.studio.servicios import trabajos as svc
    lista = svc.Lista(c / "trabajos.json")
    assert lista.por_id(ident) is not None


@requiere_binding
def test_vista_previa_de_cada_tipo(piezas, app):
    from escritorio.studio.controladores.vista import Vista
    m = piezas["muestra"]
    v = Vista(piezas["cache"])
    try:
        v.mostrar(str(m.archivos["png"]))
        assert v.tipo == "imagen" and v.url.startswith("file://") and v.descripcion.startswith("Imagen PNG")
        v.mostrar(str(m.archivos["wav"]))
        assert v.tipo == "audio" and v.url.endswith("entrevista.wav")
        v.mostrar(str(m.archivos["srt"]))
        assert v.tipo == "texto" and "Hola, buenas tardes" in v.texto
        v.mostrar(str(m.archivos["carpeta"]))
        assert v.tipo == "carpeta" and v.url == ""
        v.mostrar(str(m.archivos["pdf"]))
        if v.paginas.filas:                                   # con poppler
            assert v.tipo == "pdf" and v.paginas.filas == 2 and "2 páginas" in v.descripcion
            assert v.renderizar_ya(1).endswith(".png") and v.paginas.fila(0)["imagen"].startswith("file://")
        v.mostrar("")
        assert v.tipo == "" and v.ruta == ""
    finally:
        v.apagar()
