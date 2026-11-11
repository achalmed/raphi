"""tests/studio/test_servicios.py — los servicios de Raphi Studio sin Qt, sobre los archivos de muestra: las familias
(cada operación en una, por su ficha), las fichas (el corredor, las herramientas con su familia, las recetas como
herramientas, el Resumen en Markdown, los campos del formulario), los archivos (tipo, tamaño, vista previa, lectura
acotada), los trabajos (el archivo para el corredor, el progreso y el informe de sus líneas, el estado final, el
Resultado en Markdown, la lista persistida) y el catálogo de operaciones; un trabajo real por el corredor
(convertir subtítulos: sin programas) si el .venv está."""
from __future__ import annotations

import shutil

import json
import subprocess
from pathlib import Path

import pytest

from conftest import MOTOR, REPO, STUDIO, requiere_motor

from escritorio.studio import familias
from escritorio.studio.servicios import archivos as svc_archivos
from escritorio.studio.servicios import fichas as svc_fichas
from escritorio.studio.servicios import operaciones as ops
from escritorio.studio.servicios import rutas
from escritorio.studio.servicios import trabajos as svc_trabajos

FICHAS_MINIMAS = {"version": "0.1.0", "interprete": "python", "categorias": ["Organizar", "Medios"], "operaciones": [
    {"id": "unir", "categoria": "Organizar", "titulo": "Unir PDF", "descripcion": "Junta varios PDF.", "entrada": "pdfs", "lote": False,
     "parametros": [{"clave": "nombre", "etiqueta": "Nombre", "tipo": "texto", "defecto": "unido", "opciones": [], "minimo": None, "maximo": None, "ayuda": "sin .pdf", "obligatorio": False},
                    {"clave": "paginas", "etiqueta": "Páginas", "tipo": "paginas", "defecto": "", "opciones": [], "minimo": None, "maximo": None, "ayuda": "", "obligatorio": False}],
     "requiere": [], "faltan": [], "extensiones": [".pdf"], "minimo_entradas": 2, "palabras": ["juntar"]},
    {"id": "convertir_subtitulos", "categoria": "Medios", "titulo": "Convertir subtítulos", "descripcion": "SRT ↔ VTT.", "entrada": "medios", "lote": True,
     "parametros": [], "requiere": [], "faltan": [], "extensiones": [".srt", ".vtt"], "minimo_entradas": 1, "palabras": ["srt"]},
    {"id": "transcribir", "categoria": "Medios", "titulo": "Transcribir", "descripcion": "Whisper.", "entrada": "medios", "lote": True, "parametros": [],
     "requiere": ["whisper", "ffmpeg"], "faltan": ["whisper"], "extensiones": [".mp3"], "minimo_entradas": 1, "palabras": []}],
    "recetas": [{"id": "para-enviar", "nombre": "Para enviar", "descripcion": "", "origen": "serie", "sin_entradas": False, "entrada": "pdf", "extensiones": [".pdf"],
                 "minimo_entradas": 1, "faltan": [], "pasos": [{"operacion": "comprimir", "titulo": "Comprimir PDF", "params": {"hasta": 10}}]}]}


def test_rutas():
    assert rutas.REPO == REPO and rutas.CORREDOR.is_file() and rutas.STUDIO == STUDIO
    assert "sudo" not in rutas.orden_crear_venv() and "apt" not in rutas.orden_crear_venv()
    assert rutas.relativa(Path.home() / "x" / "y.pdf") == "~/x/y.pdf"


def test_familias_y_acepta(muestra_sesion):
    f = FICHAS_MINIMAS["operaciones"]
    assert familias.familia_de(f[0]) == "pdf" and familias.familia_de(f[1]) == "audio_video" and familias.familia_de({"id": "descargar", "entrada": "ninguna", "extensiones": []}) == "audio_video"
    assert familias.icono_de({"id": "otra_de_pdf", "entrada": "pdf", "extensiones": [".pdf"]}) == "application-pdf"   # la de su familia
    assert familias.icono_de(f[0]) == "merge" and familias.nombre_de("imagenes") == "Imágenes"                          # salvo la propia
    pdf, srt = str(muestra_sesion.archivos["pdf"]), str(muestra_sesion.archivos["srt"])
    assert familias.acepta(f[1], [srt]) and not familias.acepta(f[1], [pdf]) and not familias.acepta(f[0], [pdf]) and familias.acepta(f[0], [pdf, str(muestra_sesion.archivos["otro"])])
    assert not familias.acepta(f[0], [])


def test_areas_del_catalogo():
    """Las áreas del encargo (X1): una herramienta puede estar en varias; la suya, primero; nada queda sin área."""
    f = FICHAS_MINIMAS["operaciones"]
    assert familias.areas_de(f[0])[0] == "documentos_pdf" and "lotes" in familias.areas_de(f[0])          # unir: muchos en uno
    assert familias.areas_de(f[1]) == ["transcripcion", "conversion"]                                     # convertir subtítulos
    assert familias.areas_de(f[2])[:2] == ["transcripcion", "audio"]                                      # transcribir
    assert familias.areas_de({"es_receta": True, "id": "x"}) == ["recetas"]
    assert familias.areas_de({"id": "descargar", "entrada": "ninguna", "extensiones": [], "categoria": "Medios"})[:2] == ["video", "audio"]
    assert familias.formatos_texto(f[0]) == "PDF" and familias.formatos_texto(f[1]) == "SRT VTT"
    assert familias.formatos_texto({"id": "descargar", "entrada": "ninguna", "minimo_entradas": 0}).startswith("sin archivos")
    assert [a[1] for a in familias.AREAS] == ["Documentos y PDF", "Imágenes", "Audio", "Vídeo", "Transcripción", "Conversión",
                                              "Procesamiento por lotes", "Automatización y recetas"]


def test_vista_previa_servicio(muestra_sesion, tmp_path):
    from escritorio.studio.servicios import vista_previa as vp
    m = muestra_sesion
    assert [vp.tipo(m.archivos[k]) for k in ("png", "pdf", "wav", "srt", "md", "carpeta")] == ["imagen", "pdf", "audio", "texto", "texto", "carpeta"]
    assert vp.tipo(tmp_path / "x.mkv") == "video" and vp.tipo(tmp_path / "x.docx") == ""
    if shutil.which("pdftoppm") and shutil.which("pdfinfo"):                 # las páginas, con el visor de gui-comun 3.2
        from gui_comun import visor_pdf
        assert len(visor_pdf.paginas(m.archivos["pdf"])) == 2
        png = visor_pdf.renderizar(m.archivos["pdf"], 1, 40, tmp_path)
        assert png and png.read_bytes()[:4] == b"\x89PNG" and visor_pdf.renderizar(m.archivos["pdf"], 1, 40, tmp_path) == png
        assert visor_pdf.podar(tmp_path, limite=0) > 0


def test_fichas_herramientas_resumen_y_campos():
    h = svc_fichas.herramientas(FICHAS_MINIMAS)
    assert [x["ref"] for x in h] == ["unir", "convertir_subtitulos", "transcribir", "receta:para-enviar"]
    assert h[0]["familia"] == "pdf" and h[2]["larga"] and not h[0]["larga"] and h[3]["es_receta"] and h[3]["familia"] == "recetas" and h[3]["entrada"] == "pdf"
    assert svc_fichas.acepta_texto(h[0]) == "PDF" and svc_fichas.entrada_texto(h[0]) == "2 o más (todos juntos)" and svc_fichas.entrada_texto(h[1]).startswith("uno o más (cada")
    md = svc_fichas.resumen_markdown(h[0])
    assert md.startswith("# Unir PDF") and "**Recibe**: 2 o más (todos juntos) · PDF" in md and "- **Nombre** (`nombre`, texto, por omisión `unido`): sin .pdf" in md
    assert "**Falta en esta máquina**: whisper" in svc_fichas.resumen_markdown(h[2]) and "**Tarda**" in svc_fichas.resumen_markdown(h[2])
    assert "**Pasos**: Comprimir PDF" in svc_fichas.resumen_markdown(h[3])
    campos = svc_fichas.campos_formulario(h[0])
    assert campos[0]["tipo"] == "texto" and campos[1]["tipo"] == "texto" and campos[1]["marcador"] == "todas · 1-3,5 · último"


def test_archivos(muestra_sesion):
    m = muestra_sesion.archivos
    f = svc_archivos.fila_de(m["pdf"])
    assert f["nombre"] == "oficio.pdf" and f["tipo"] == "PDF" and f["existe"] and f["tamano"].endswith("B")
    assert svc_archivos.fila_de(m["carpeta"])["tipo"] == "Carpeta"
    assert svc_archivos.vista_previa(m["png"]) == "imagen" and svc_archivos.vista_previa(m["srt"]) == "texto" and svc_archivos.vista_previa(m["pdf"]) == ""
    assert "Hola, buenas tardes." in svc_archivos.leer_texto(m["srt"]) and "No se pudo leer" in svc_archivos.leer_texto(m["pdf"].parent / "no.txt")
    assert svc_archivos.tamano_legible(1536) == "1.5 KB" and svc_archivos.tamano_legible(None) == "—"


def test_trabajos_servicio(tmp_path):
    t = svc_trabajos.nuevo("receta:para-enviar", "Para enviar", ["/a.pdf"], {}, "", True)
    assert t.es_receta and t.para_corredor() == {"archivos": ["/a.pdf"], "params": {}, "destino": "", "simular": True, "receta": "para-enviar"}
    assert svc_trabajos.progreso_de("## progreso 45 Rotando") == (45, "Rotando") and svc_trabajos.progreso_de("hola") is None
    informe = {"ok": False, "correctos": 1, "fallidos": 1, "simulado": False, "elementos": [{"entrada": "/a.pdf", "ok": True, "archivos": ["/a_x.pdf"], "plan": [], "mensajes": [], "error": ""},
                                                                                             {"entrada": "/b.pdf", "ok": False, "error": "roto", "archivos": [], "plan": [], "mensajes": []}]}
    archivo = tmp_path / "t.informe.json"
    archivo.write_text(json.dumps(informe), encoding="utf-8")
    assert svc_trabajos.informe_de(["x", f"## informe {archivo}"]) == informe and svc_trabajos.informe_de(['## informe {"ok": true}']) == {"ok": True}
    assert svc_trabajos.estado_final(1, informe, False) == ("parcial", "1 correcto(s), 1 con error")
    assert svc_trabajos.estado_final(0, {"ok": True, "correctos": 2, "fallidos": 0, "simulado": True, "elementos": []}, False) == ("hecho", "plan de 2 elemento(s)")
    assert svc_trabajos.estado_final(130, None, True) == ("cancelado", "Cancelado.") and svc_trabajos.estado_final(2, None, False)[0] == "fallido"
    t.informe, t.simular = informe, False
    md = svc_trabajos.texto_resultado(t)
    assert "### ✓ a.pdf" in md and "- → `a_x.pdf` en `/`" in md and "### ✗ b.pdf" in md and "**Error**: roto" in md
    lista = svc_trabajos.Lista(tmp_path / "trabajos.json")
    lista.anadir(t)
    t.estado = "en_curso"
    lista.guardar()
    otra = svc_trabajos.Lista(tmp_path / "trabajos.json")
    assert otra.por_id(t.id).estado == "cancelado" and otra.contar()["todos"] == 1 and otra.siguiente_en_cola() is None


def test_operaciones_catalogo():
    assert [o.id for o in ops.OPERACIONES] == ["herramienta", "doctor", "lista", "formatos"]
    h = ops.operacion("herramienta")
    assert h.trabajo and h.escribe and h.verbo == "Simular" and ops.operacion("doctor").cli([]).texto() == "python -m raphi doctor"
    assert ops.operacion("formatos").cli(["/x/a.heic"]).argv[-1] == "/x/a.heic" and ops.operacion("formatos").sobre_archivos


@requiere_motor
def test_corredor_fichas_y_un_trabajo_real(muestra_sesion, tmp_path):
    datos = svc_fichas.pedir(MOTOR)
    assert datos["version"] and len(datos["operaciones"]) >= 60 and any(r["id"] == "para-enviar" for r in datos["recetas"])
    h = {x["ref"]: x for x in svc_fichas.herramientas(datos)}
    assert set(familias.NOMBRES) >= {x["familia"] for x in h.values()}
    srt = tmp_path / "entrevista.srt"
    srt.write_bytes(muestra_sesion.archivos["srt"].read_bytes())
    for simular in (True, False):
        t = svc_trabajos.nuevo("convertir_subtitulos", "Convertir subtítulos", [str(srt)], {}, "", simular)
        archivo = tmp_path / f"{t.id}.json"
        archivo.write_text(json.dumps(t.para_corredor()), encoding="utf-8")
        r = subprocess.run([MOTOR, str(rutas.CORREDOR), "ejecutar", str(archivo)], capture_output=True, text=True, timeout=120, cwd=str(REPO))
        assert r.returncode == 0, r.stderr[-1500:]
        informe = svc_trabajos.informe_de(r.stdout.splitlines())
        assert informe and informe["ok"] and informe["simulado"] is simular
        assert svc_trabajos.estado_final(0, informe, False)[0] == "hecho"
    assert (tmp_path / "entrevista.vtt").is_file() and srt.read_bytes() == muestra_sesion.archivos["srt"].read_bytes()     # el original no se toca
