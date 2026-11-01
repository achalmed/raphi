"""Las operaciones que envuelven los backends de medios: descargar, transcribir, acortar subtítulos y fotos (2026-10-31)."""
from __future__ import annotations

import shutil
import subprocess

import pytest

from raphi import motor
from raphi.__main__ import _expandir
from raphi.motor.base import REGISTRO, obtener

NUEVAS = ("descargar", "transcribir", "ajustar_subtitulos", "auditar_fechas_fotos", "ordenar_fotos_por_fecha")



def test_estan_registradas_con_su_ficha():
    for id in NUEVAS:
        ficha = obtener(id).ficha()
        assert ficha["titulo"] and ficha["descripcion"], id
    assert "audio_converter" not in REGISTRO   # el conversor retirado no vuelve como operación


def test_descargar_simula_sin_red_ni_escritura(tmp_path):
    inf = motor.ejecutar("descargar", [], {"url": "https://example.org/a\nhttps://example.org/b"}, destino=tmp_path,
                         simular=True)
    assert inf.ok and len(inf.elementos[0].resultado.plan) == 2
    assert not any(tmp_path.iterdir())


def test_descargar_sin_enlace_es_error_claro():
    with pytest.raises(motor.ErrorOperacion):
        motor.ejecutar("descargar", [], {}, simular=True)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="falta ffmpeg")
def test_transcribir_simula(tmp_path):
    audio = tmp_path / "a.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "sine=duration=1", str(audio)], check=True)
    inf = motor.ejecutar("transcribir", [audio], {"formato": "txt"}, simular=True)
    assert inf.ok and "a.txt" in inf.elementos[0].resultado.plan[0]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["a.wav"]


@pytest.mark.skipif(not obtener("ajustar_subtitulos").faltan() == [], reason="falta pysrt")
def test_ajustar_subtitulos_no_toca_el_original(tmp_path):
    srt = tmp_path / "s.srt"
    srt.write_text("1\n00:00:01,000 --> 00:00:04,000\n" + "palabra " * 20 + "\n\n", encoding="utf-8")
    antes = srt.read_bytes()
    inf = motor.ejecutar("ajustar_subtitulos", [srt], {"largo": 25})
    assert inf.ok, inf.elementos[0].error
    salida = inf.archivos[0]
    assert srt.read_bytes() == antes and salida != srt
    assert all(len(l) <= 25 for l in salida.read_text(encoding="utf-8").splitlines() if "-->" not in l)


@pytest.mark.skipif(bool(obtener("ordenar_fotos_por_fecha").faltan()), reason="falta exiftool")
def test_ordenar_fotos_trabaja_sobre_una_copia(tmp_path):
    from PIL import Image
    carpeta = tmp_path / "fotos"
    carpeta.mkdir()
    Image.new("RGB", (16, 16), "red").save(carpeta / "IMG-20250314-WA0007.jpg")
    Image.new("RGB", (16, 16), "blue").save(carpeta / "Screenshot_20240102-101112.jpg", "PNG")   # extensión falsa
    antes = sorted(p.name for p in carpeta.iterdir())
    inf = motor.ejecutar("ordenar_fotos_por_fecha", [carpeta], {})
    assert inf.ok, inf.elementos[0].error
    assert sorted(p.name for p in carpeta.iterdir()) == antes            # el original, intacto
    nombres = {p.name for p in inf.archivos[0].iterdir()}
    assert {"20240102_101112.png", "20250314_wa0007.jpg"} <= nombres


def test_la_cli_expande_carpetas_segun_la_operacion(tmp_path):
    (tmp_path / "sub").mkdir()
    for n in ("a.mp3", "b.txt", "sub/c.ogg"):
        (tmp_path / n).write_bytes(b"x")
    audio = obtener("convertir_audio")
    assert [p.split("/")[-1] for p in _expandir([str(tmp_path)], audio, False)] == ["a.mp3"]
    assert {p.split("/")[-1] for p in _expandir([str(tmp_path)], audio, True)} == {"a.mp3", "c.ogg"}
    assert _expandir([str(tmp_path)], obtener("ordenar_fotos_por_fecha"), False) == [str(tmp_path)]
