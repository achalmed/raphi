"""El motor: cada operación con su corpus, y los tres principios (error por archivo, original intacto, simular)."""
from __future__ import annotations

import hashlib
import shutil

import pikepdf
import pytest

from raphi import motor
from raphi.motor.base import ErrorOperacion, paginas_de
from raphi.motor.utiles import interpretar_paginas


def huella(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def correr(op, entradas, salida, **params):
    inf = motor.ejecutar(op, entradas, params, destino=salida)
    assert inf.ok, [e.error for e in inf.elementos]
    return inf


# --- principios ---------------------------------------------------------------------------------------------------


def test_todas_las_operaciones_tienen_ficha_completa():
    assert len(motor.REGISTRO) >= 45
    for f in motor.operaciones():
        assert f["titulo"] and f["descripcion"] and f["categoria"]
        assert all(p["etiqueta"] for p in f["parametros"])


def test_simular_no_escribe_nada(corpus, salida):
    for op in ("comprimir", "rotar", "foliar", "ocr", "pdfa", "dividir"):
        inf = motor.ejecutar(op, [corpus["texto"]], {}, destino=salida, simular=True)
        assert inf.simulado and inf.ok and inf.elementos[0].resultado.plan
    assert not salida.exists()


def test_error_por_archivo_no_detiene_el_lote(corpus, salida):
    inf = motor.ejecutar("rotar", [corpus["texto"], corpus["nopdf"], corpus["otro"]], {}, destino=salida)
    assert [e.ok for e in inf.elementos] == [True, False, True]
    assert "no se puede leer" in inf.elementos[1].error
    assert len(inf.archivos) == 2


def test_el_original_nunca_se_toca(corpus, tmp_path):
    copia = tmp_path / "doc.pdf"
    shutil.copy(corpus["texto"], copia)
    antes = huella(copia)
    for op in ("rotar", "foliar", "metadatos", "quitar_metadatos"):
        params = {"titulo": "X"} if op == "metadatos" else {}
        inf = motor.ejecutar(op, [copia], params)          # sin destino: junto al original, con sufijo
        assert inf.ok, inf.elementos[0].error
        assert inf.archivos[0] != copia and inf.archivos[0].parent == tmp_path
    assert huella(copia) == antes


def test_salidas_no_se_pisan(corpus, salida):
    a = correr("rotar", [corpus["texto"]], salida).archivos[0]
    b = correr("rotar", [corpus["texto"]], salida).archivos[0]
    assert a != b and b.name.endswith("-2.pdf")


def test_parametros_se_validan():
    with pytest.raises(ErrorOperacion, match="uno de"):
        motor.ejecutar("rotar", ["x.pdf"], {"angulo": "45"})
    with pytest.raises(ErrorOperacion, match="desconocidos"):
        motor.ejecutar("rotar", ["x.pdf"], {"nada": 1})


def test_rangos_de_paginas():
    assert interpretar_paginas("1-3,5,z", 10) == [0, 1, 2, 4, 9]
    assert interpretar_paginas("-2", 10) == [8, 9]
    assert interpretar_paginas("", 3) == [0, 1, 2]
    assert interpretar_paginas("3-1", 5) == [2, 1, 0]
    with pytest.raises(ErrorOperacion):
        interpretar_paginas("12", 10)


# --- organizar ----------------------------------------------------------------------------------------------------


def test_unir_dividir_extraer_reordenar_eliminar(corpus, salida):
    unido = correr("unir", [corpus["texto"], corpus["otro"]], salida).archivos[0]
    assert paginas_de(unido) == 5
    with pikepdf.open(unido) as pdf:
        assert [i.title for i in pdf.open_outline().root] == ["texto", "otro"]
    partes = correr("dividir", [corpus["texto"]], salida, cada=2).archivos
    assert [paginas_de(p) for p in partes] == [2, 1]
    partes = correr("dividir", [corpus["texto"]], salida, rangos="1; 2-z").archivos
    assert [paginas_de(p) for p in partes] == [1, 2]
    assert paginas_de(correr("extraer", [corpus["largo"]], salida, paginas="10-12,z").archivos[0]) == 4
    r = correr("reordenar", [corpus["texto"]], salida, orden="3").archivos[0]
    import pymupdf
    with pymupdf.open(r) as doc:
        assert doc[0].get_text().startswith("Página 3")
    assert paginas_de(correr("eliminar", [corpus["texto"]], salida, paginas="2").archivos[0]) == 2
    inf = motor.ejecutar("eliminar", [corpus["texto"]], {"paginas": "1-z"}, destino=salida)
    assert not inf.ok and "todas" in inf.elementos[0].error


def test_rotar_y_componer(corpus, salida):
    r = correr("rotar", [corpus["texto"]], salida, angulo="90", paginas="2").archivos[0]
    with pikepdf.open(r) as pdf:
        assert [int(p.obj.get("/Rotate", 0)) for p in pdf.pages] == [0, 90, 0]
    plan = [{"archivo": 1, "pagina": 2}, {"blanca": True}, {"archivo": 0, "pagina": 1, "rotar": 180}]
    c = correr("componer", [corpus["texto"], corpus["otro"]], salida, plan=plan).archivos[0]
    assert paginas_de(c) == 3


# --- optimizar ---------------------------------------------------------------------------------------------------


def test_comprimir_escaneo_y_sin_ganancia(corpus, salida):
    inf = correr("comprimir", [corpus["escaneo"]], salida, perfil="screen", umbral=0)
    e = inf.elementos[0].resultado
    assert e.sin_cambio or e.datos["final"] < e.datos["original"]
    inf = correr("comprimir", [corpus["texto"]], salida, umbral=90)      # un PDF de texto apenas baja
    assert inf.elementos[0].resultado.sin_cambio and not inf.archivos


def test_comprimir_hasta_un_tope(corpus, salida):
    inf = correr("comprimir", [corpus["escaneo"]], salida, hasta="0.05", umbral=0)
    assert inf.elementos[0].resultado.datos["metodo"]


def test_reparar_validar_pdfa_linearizar(corpus, salida):
    rep = correr("reparar", [corpus["danado"]], salida).archivos[0]
    assert paginas_de(rep) == 3
    v = correr("validar", [corpus["texto"]], salida).elementos[0].resultado
    assert v.datos["valido"] is True and not v.archivos
    a = correr("pdfa", [corpus["texto"]], salida).archivos[0]
    from raphi.motor.pdf_optimizar import es_pdfa
    assert es_pdfa(a) == "2B"
    w = correr("linearizar", [corpus["texto"]], salida).archivos[0]
    with pikepdf.open(w) as pdf:
        assert pdf.is_linearized


# --- editar y seguridad --------------------------------------------------------------------------------------------


def test_foliar_numerar_sello_marca(corpus, salida):
    import pymupdf
    f = correr("foliar", [corpus["texto"]], salida, inicio=41, orden="inverso").archivos[0]
    with pymupdf.open(f) as doc:
        textos = [p.get_text() for p in doc]
    assert "43" in textos[0] and "41" in textos[2]
    n = correr("numerar", [corpus["texto"]], salida, formato="Pág. {n} de {total}", desde=2).archivos[0]
    with pymupdf.open(n) as doc:
        assert "Pág. 1 de 2" in doc[1].get_text() and "Pág." not in doc[0].get_text()
    s = correr("sello", [corpus["texto"]], salida, entidad="Mesa de Partes", fecha="27/10/2026 10:00").archivos[0]
    with pymupdf.open(s) as doc:
        t = doc[0].get_text()
    assert "RECIBIDO" in t and "27/10/2026 10:00" in t and "Folios: 3" in t
    m = correr("marca_agua", [corpus["texto"]], salida, texto="CONFIDENCIAL").archivos[0]
    with pymupdf.open(m) as doc:
        assert "CONFIDENCIAL" in doc[0].get_text()
    inf = motor.ejecutar("numerar", [corpus["texto"]], {"formato": "{x}"}, destino=salida)
    assert not inf.ok and "{n}" in inf.elementos[0].error


def test_foliar_respeta_paginas_rotadas(corpus, salida):
    import pymupdf
    r = correr("rotar", [corpus["texto"]], salida, angulo="90").archivos[0]
    f = correr("foliar", [r], salida, inicio=7).archivos[0]
    with pymupdf.open(f) as doc:
        p = doc[0]
        palabras = [w for w in p.get_text("words") if w[4] == "7"]
        assert palabras, "el folio no se escribió"
        visible = pymupdf.Rect(palabras[0][:4]) * p.rotation_matrix
        assert visible.x0 > p.rect.width / 2 and visible.y0 < p.rect.height / 2     # arriba a la derecha, como se ve


def test_cifrar_descifrar_metadatos_firmas(corpus, salida):
    c = correr("cifrar", [corpus["texto"]], salida, clave="secreta").archivos[0]
    with pytest.raises(pikepdf.PasswordError):
        pikepdf.open(c)
    inf = motor.ejecutar("descifrar", [c], {"clave": "mala"}, destino=salida)
    assert not inf.ok and "contraseña" in inf.elementos[0].error
    d = correr("descifrar", [c], salida, clave="secreta").archivos[0]
    assert paginas_de(d) == 3
    inf = motor.ejecutar("rotar", [corpus["cifrado"]], {}, destino=salida)
    assert not inf.ok and "contraseña" in inf.elementos[0].error
    m = correr("metadatos", [corpus["texto"]], salida, titulo="Oficio de prueba", autor="Raphi").archivos[0]
    with pikepdf.open(m) as pdf:
        assert pdf.open_metadata()["dc:title"] == "Oficio de prueba"
    q = correr("quitar_metadatos", [m], salida).archivos[0]
    with pikepdf.open(q) as pdf:
        assert "/Metadata" not in pdf.Root and not pdf.docinfo.get("/Title")
    f = correr("firmas", [corpus["texto"]], salida).elementos[0].resultado
    assert f.datos["firmas"] == []


# --- contenido -------------------------------------------------------------------------------------------------


def test_pdf_a_imagen_texto_html_miniatura(corpus, salida):
    carpeta = correr("pdf_a_imagen", [corpus["texto"]], salida, ppp=50, paginas="1-2").archivos[0]
    assert len(list(carpeta.glob("*.png"))) == 2
    t = correr("pdf_a_texto", [corpus["texto"]], salida).archivos[0]
    assert "acción" in t.read_text()
    h = correr("pdf_a_html", [corpus["texto"]], salida).archivos[0]
    assert "<section" in h.read_text()
    for fmt in ("png", "webp"):
        assert correr("miniatura", [corpus["texto"]], salida, formato=fmt).archivos[0].suffix == f".{fmt}"


def test_detectar_ocr_y_ocr(corpus, salida):
    d = correr("detectar_ocr", [corpus["escaneo"]], salida).elementos[0].resultado
    assert d.datos["necesita_ocr"] == "sí"
    assert correr("detectar_ocr", [corpus["texto"]], salida).elementos[0].resultado.datos["necesita_ocr"] == "no"
    o = correr("ocr", [corpus["escaneo"]], salida, optimizar=0).archivos[0]
    import pymupdf
    with pymupdf.open(o) as doc:
        assert "OFICIO" in doc[0].get_text().upper()


def test_extraer_imagenes(corpus, salida):
    assert correr("extraer_imagenes", [corpus["escaneo"]], salida).archivos
    assert correr("extraer_imagenes", [corpus["texto"]], salida).elementos[0].resultado.sin_cambio


# --- información e inventario --------------------------------------------------------------------------------------


def test_info(corpus, salida):
    d = correr("info", [corpus["texto"]], salida).elementos[0].resultado.datos
    assert d["paginas"] == 3 and d["tamanos"] == {"A4": 3} and d["con_texto"] == 3
    assert correr("info", [corpus["cifrado"]], salida).elementos[0].resultado.datos["cifrado"] is True


def test_inventario_de_paginas(corpus, tmp_path):
    carpeta = tmp_path / "pubs" / "blog-a"
    carpeta.mkdir(parents=True)
    shutil.copy(corpus["texto"], carpeta / "index.pdf")
    shutil.copy(corpus["otro"], carpeta / "anexo.pdf")
    inf = correr("inventario_paginas", [carpeta, corpus["largo"]], tmp_path, nombre="inv")
    from openpyxl import load_workbook
    hoja = load_workbook(inf.archivos[0])["Conteo de Páginas"]
    valores = [c.value for c in hoja["C"] if isinstance(c.value, int)]
    assert valores[-1] == 305 and inf.elementos[0].resultado.datos["archivos"] == 3
    solo = correr("inventario_paginas", [carpeta], tmp_path, solo_index=True, nombre="inv2").elementos[0].resultado
    assert solo.datos["paginas"] == 3


def test_fuente_hub_del_espacio_de_trabajo():
    from raphi.fuentes import hub
    if not hub.hay():
        pytest.skip("fuera del espacio de trabajo")
    assert isinstance(hub.blogs(), dict)


# --- documentos ----------------------------------------------------------------------------------------------------


def test_imagenes_a_pdf(corpus, salida):
    p = correr("imagenes_a_pdf", [corpus["jpg"], corpus["png"]], salida, papel="A4").archivos[0]
    assert paginas_de(p) == 2


@pytest.mark.skipif(not shutil.which("soffice"), reason="sin LibreOffice")
def test_documento_a_pdf_y_ofimatica(corpus, salida):
    p = correr("a_pdf", [corpus["txt"]], salida).archivos[0]
    assert paginas_de(p) == 1
    o = correr("ofimatica", [corpus["txt"]], salida, formato="odt").archivos[0]
    assert o.suffix == ".odt"
