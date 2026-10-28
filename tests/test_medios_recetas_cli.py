"""Medios (R5), el menú de Tangerine, las recetas y la CLI."""
from __future__ import annotations

import json
import shutil

import pytest

from raphi import motor, recetas
from raphi.__main__ import main
from raphi.motor.base import paginas_de
from raphi.motor.medios import formatos_de


def correr(op, entradas, salida, **params):
    inf = motor.ejecutar(op, entradas, params, destino=salida)
    assert inf.ok, [e.error for e in inf.elementos]
    return inf


def test_imagenes(corpus, salida):
    from PIL import Image
    for fmt in ("png", "webp", "avif", "heic"):
        a = correr("convertir_imagen", [corpus["jpg"]], salida, formato=fmt).archivos[0]
        assert a.suffix == f".{fmt}"
    heic = next(salida.glob("*.heic"))
    j = correr("convertir_imagen", [heic], salida, formato="jpg").archivos[0]
    with Image.open(j) as img:
        assert img.size == (800, 600)
    r = correr("redimensionar_imagen", [corpus["jpg"]], salida, ancho=400).archivos[0]
    with Image.open(r) as img:
        assert img.size == (400, 300)
    c = correr("recortar_imagen", [corpus["jpg"]], salida, proporcion="1:1").archivos[0]
    with Image.open(c) as img:
        assert img.size == (600, 600)
    inf = motor.ejecutar("recortar_imagen", [corpus["jpg"]], {"proporcion": "libre", "caja": "0,0,900,10"}, destino=salida)
    assert not inf.ok and "se sale" in inf.elementos[0].error
    correr("comprimir_imagen", [corpus["jpg"]], salida, calidad=40)
    # Un PNG de colores planos pesa más como JPG: no se da por comprimido.
    plano = salida / "plano.png"
    Image.new("RGB", (800, 600), (30, 120, 200)).save(plano, optimize=True)
    inf = correr("comprimir_imagen", [plano], salida / "sin")
    assert inf.elementos[0].resultado.sin_cambio and not list((salida / "sin").glob("*"))


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="sin ffmpeg")
def test_audio_video(corpus, salida):
    from raphi.motor.medios import duracion
    m = correr("convertir_audio", [corpus["wav"]], salida, formato="mp3").archivos[0]
    assert m.suffix == ".mp3" and duracion(m) > 1.5
    w = correr("convertir_video", [corpus["mp4"]], salida, formato="webm").archivos[0]
    assert duracion(w) > 1.5
    g = correr("convertir_video", [corpus["mp4"]], salida, formato="gif", ancho=160).archivos[0]
    assert g.stat().st_size > 0
    r = correr("recortar_medio", [corpus["mp4"]], salida, desde="0.5", hasta="1.5", exacto=True).archivos[0]
    assert 0.8 < duracion(r) < 1.3
    correr("comprimir_video", [corpus["mp4"]], salida, calidad=32)
    correr("convertir_video", [corpus["mp4"]], salida, formato="m4a")


def test_subtitulos_ida_y_vuelta(corpus, salida):
    v = correr("convertir_subtitulos", [corpus["srt"]], salida).archivos[0]
    assert v.read_text().startswith("WEBVTT") and "00:00:01.000 --> 00:00:02.500" in v.read_text()
    s = correr("convertir_subtitulos", [v], salida).archivos[0]
    assert "00:00:01,000 --> 00:00:02,500" in s.read_text() and "Mundo" in s.read_text()


def test_archivos_comprimidos(corpus, tmp_path):
    carpeta = tmp_path / "datos"
    carpeta.mkdir()
    shutil.copy(corpus["texto"], carpeta / "a.pdf")
    for fmt in ("zip", "tar.gz", "7z"):
        if fmt == "7z" and not shutil.which("7z"):
            continue
        z = correr("comprimir_archivos", [carpeta, corpus["jpg"]], tmp_path / "out", formato=fmt,
                   nombre=f"paq-{fmt[:3]}").archivos[0]
        x = correr("extraer_archivo", [z], tmp_path / f"ext-{fmt[:3]}").archivos[0]
        assert (x / "datos" / "a.pdf").is_file() and (x / "foto.jpg").is_file()


@pytest.mark.skipif(not shutil.which("exiftool"), reason="sin exiftool")
def test_quitar_metadatos_de_una_foto(corpus, salida):
    correr("quitar_metadatos_archivo", [corpus["jpg"]], salida)


def test_menu_de_tangerine(corpus):
    foto = {f["a"] for f in formatos_de(corpus["jpg"]) if f["a"]}
    assert {"png", "webp", "heic", "pdf"} <= foto and "jpg" not in foto
    pdf = {f["operacion"] for f in formatos_de(corpus["texto"])}
    assert {"pdf_a_word", "comprimir", "ocr", "foliar"} <= pdf
    assert {f["a"] for f in formatos_de(corpus["srt"]) if f["a"]} >= {"vtt"}
    from pathlib import Path
    texto = {f["a"] for f in formatos_de(Path("carta.docx")) if f["operacion"] == "ofimatica"}
    assert texto == {"odt", "rtf", "txt", "html"}                    # un texto no se vuelve hoja ni presentación
    assert {f["a"] for f in formatos_de(Path("cuadro.ods")) if f["operacion"] == "ofimatica"} == {"xlsx", "html"}


def test_ofimatica_rechaza_otra_familia(corpus, salida):
    inf = motor.ejecutar("ofimatica", [corpus["txt"]], {"formato": "xlsx"}, destino=salida)
    assert not inf.ok and "no a .xlsx" in inf.elementos[0].error


# --- recetas -----------------------------------------------------------------------------------------------------


def test_recetas_de_serie_validas():
    ids = {r.id for r in recetas.todas()}
    assert {"escaneo-mesa-de-partes", "para-enviar", "para-archivo", "paginas-de-los-blogs"} <= ids


def test_receta_encadena_y_sigue_si_un_paso_no_cambia(corpus, tmp_path):
    r = recetas.desde_dict({"nombre": "prueba", "pasos": [
        {"operacion": "comprimir", "params": {"umbral": 95}},         # no gana: deja pasar
        {"operacion": "rotar", "params": {"angulo": "180"}},
        {"operacion": "foliar", "params": {"inicio": 7}}]}, "prueba")
    inf = recetas.aplicar(r, [corpus["texto"], corpus["nopdf"]], destino=tmp_path / "fin")
    assert [e.ok for e in inf.elementos] == [True, False]
    final = inf.archivos[0]
    assert final.name == "texto_prueba.pdf" and paginas_de(final) == 3
    assert not list((tmp_path / "fin").glob("*rotado*"))       # los intermedios no se quedan


def test_receta_simulada_no_escribe(corpus, tmp_path):
    inf = recetas.aplicar(recetas.buscar("para-archivo"), [corpus["texto"]], destino=tmp_path / "x", simular=True)
    assert inf.simulado and inf.elementos[0].resultado.plan and not (tmp_path / "x").exists()


def test_receta_invalida_se_rechaza():
    with pytest.raises(motor.ErrorOperacion, match="Paso 1"):
        recetas.desde_dict({"pasos": [{"operacion": "rotar", "params": {"angulo": "7"}}]})


def test_guardar_receta_del_usuario(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    r = recetas.desde_dict({"nombre": "Mía", "pasos": [{"operacion": "pdfa"}]}, "mia")
    ruta = recetas.guardar(r)
    assert ruta.is_file() and recetas.buscar("mia").nombre == "Mía"


# --- CLI ---------------------------------------------------------------------------------------------------------


def test_cli(corpus, tmp_path, capsys):
    assert main(["lista"]) == 0 and "Foliar expediente" in capsys.readouterr().out
    assert main(["rotar", str(corpus["texto"]), "-o", str(tmp_path), "-n"]) == 0
    assert not list(tmp_path.glob("*.pdf"))
    capsys.readouterr()
    assert main(["foliar", str(corpus["texto"]), "-o", str(tmp_path), "--inicio", "5", "--no-recuadro", "--json"]) == 0
    informe = json.loads(capsys.readouterr().out)
    assert informe["ok"] and informe["elementos"][0]["archivos"]
    assert main(["rotar", str(corpus["nopdf"]), "-o", str(tmp_path)]) == 1
    assert main(["no-existe"]) == 2
    assert main(["receta", "para-enviar", str(corpus["texto"]), "-o", str(tmp_path / "r"), "-n"]) == 0
    capsys.readouterr()
    assert main(["formatos", str(corpus["jpg"])]) == 0 and "convertir_imagen" in capsys.readouterr().out


def test_la_referencia_de_operaciones_esta_al_dia():
    from raphi.__main__ import REFERENCIA, referencia_md
    assert REFERENCIA.read_text(encoding="utf-8") == referencia_md(), "python -m raphi referencia --aplicar"
