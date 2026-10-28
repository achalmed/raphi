"""La API, la cola y el módulo de Tiqsi: en modo escritorio (ficha), en modo sola (cuentas) y como capacidad."""
from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

FICHA = "ficha-de-prueba-con-largo-suficiente-0123456789"


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    monkeypatch.setenv("RAPHI_DIR", str(tmp_path / "raphi"))
    monkeypatch.delenv("RAPHI_DATABASE_URL", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    yield tmp_path


@pytest.fixture
def escritorio(entorno):
    import asyncio
    from raphi import config as configuracion
    from raphi import db
    import raphi.escritorio as esc
    configuracion.recargar()
    app = esc.crear_app(FICHA)
    with TestClient(app) as c:
        c.headers["Authorization"] = f"Bearer {FICHA}"
        yield c
    asyncio.run(db.cerrar())


def esperar(c, ident, tope=60):
    inicio = time.monotonic()
    while time.monotonic() - inicio < tope:
        t = c.get(f"/api/raphi/trabajos/{ident}").json()
        if t["estado"] not in ("pendiente", "en_curso"):
            return t
        time.sleep(0.1)
    raise TimeoutError(ident)


def test_sin_ficha_no_entra(escritorio):
    r = escritorio.get("/api/raphi/operaciones", headers={"Authorization": "Bearer otra"})
    assert r.status_code == 401


def test_docflow_en_sistema(escritorio, entorno, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(entorno / "cache"))
    (entorno / "cache" / "docflow").mkdir(parents=True)
    (entorno / "cache" / "docflow" / "index.tsv").write_text("a\tb\nc\td\n")
    d = escritorio.get("/api/raphi/sistema").json()["docflow"]
    assert d["entradas"] == 2 and d["version"].startswith("docflow") and not d["config_existe"]
    r = escritorio.post("/api/raphi/sistema/docflow/cache", json={"vaciar": True})
    assert r.status_code == 200 and r.json()["docflow"]["entradas"] == 0


def test_operaciones_y_formatos(escritorio):
    d = escritorio.get("/api/raphi/operaciones").json()
    assert d["modo"] == "escritorio" and len(d["operaciones"]) >= 45 and "Organizar" in d["categorias"]
    f = escritorio.get("/api/raphi/formatos", params={"nombre": "foto.heic"}).json()
    assert any(x["a"] == "jpg" for x in f)


def test_subir_trabajar_descargar(escritorio, corpus):
    with open(corpus["texto"], "rb") as a, open(corpus["otro"], "rb") as b:
        fichas = escritorio.post("/api/raphi/archivos", files=[("archivos", ("Oficio Nº 1.pdf", a, "application/pdf")),
                                                               ("archivos", ("anexo.pdf", b, "application/pdf"))]).json()
    assert [f["paginas"] for f in fichas] == [3, 2]
    ids = [f["id"] for f in fichas]
    m = escritorio.get(f"/api/raphi/archivos/{ids[0]}/miniatura", params={"ancho": 120})
    assert m.status_code == 200 and m.headers["content-type"] == "image/webp"
    t = escritorio.post("/api/raphi/trabajos", json={"operacion": "unir", "archivos": ids}).json()
    t = esperar(escritorio, t["id"])
    assert t["estado"] == "hecho" and t["salidas"][0]["nombre"] == "unido.pdf"
    pdf = escritorio.get(f"/api/raphi/trabajos/{t['id']}/salidas/0")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    z = escritorio.get(f"/api/raphi/trabajos/{t['id']}/zip")
    assert z.headers["content-type"] == "application/zip"
    # Encadenar a mano: la salida vuelve a ser entrada.
    nuevo = escritorio.post(f"/api/raphi/trabajos/{t['id']}/salidas/0/a-archivo").json()
    t2 = esperar(escritorio, escritorio.post("/api/raphi/trabajos", json={"operacion": "foliar",
                                                                          "archivos": [nuevo["id"]]}).json()["id"])
    assert t2["estado"] == "hecho"
    assert [x["id"] for x in escritorio.get("/api/raphi/trabajos").json()][:2] == [t2["id"], t["id"]]


def test_parametros_malos_y_fallos_por_archivo(escritorio, corpus):
    with open(corpus["texto"], "rb") as a, open(corpus["nopdf"], "rb") as b:
        ids = [f["id"] for f in escritorio.post("/api/raphi/archivos", files=[("archivos", ("a.pdf", a)),
                                                                              ("archivos", ("b.pdf", b))]).json()]
    r = escritorio.post("/api/raphi/trabajos", json={"operacion": "rotar", "archivos": ids, "params": {"angulo": "7"}})
    assert r.status_code == 422
    assert escritorio.post("/api/raphi/trabajos", json={"operacion": "nada", "archivos": ids}).status_code == 404
    t = esperar(escritorio, escritorio.post("/api/raphi/trabajos", json={"operacion": "rotar", "archivos": ids}).json()["id"])
    assert t["estado"] == "parcial" and len(t["salidas"]) == 1


def test_archivos_locales_y_destino_junto(escritorio, corpus, tmp_path):
    import shutil
    propio = tmp_path / "mis-docs"
    propio.mkdir()
    shutil.copy(corpus["texto"], propio / "carta.pdf")
    f = escritorio.post("/api/raphi/locales", json={"rutas": [str(propio / "carta.pdf")]}).json()[0]
    assert f["local"] and f["ruta"].endswith("carta.pdf")
    t = esperar(escritorio, escritorio.post("/api/raphi/trabajos", json={
        "operacion": "foliar", "archivos": [f["id"]], "destino": "junto"}).json()["id"])
    assert t["estado"] == "hecho" and (propio / "carta_foliado.pdf").is_file()
    escritorio.delete(f"/api/raphi/archivos/{f['id']}")
    assert (propio / "carta.pdf").is_file()                    # borrar la referencia no borra el archivo del disco


def test_receta_por_la_api(escritorio, corpus):
    r = escritorio.post("/api/raphi/recetas", json={"id": "mia", "nombre": "Mía", "pasos": [
        {"operacion": "rotar", "params": {"angulo": "90"}}, {"operacion": "foliar"}]})
    assert r.status_code == 200
    assert escritorio.post("/api/raphi/recetas", json={"id": "mala", "nombre": "x", "pasos": [
        {"operacion": "rotar", "params": {"angulo": "7"}}]}).status_code == 422
    with open(corpus["texto"], "rb") as a:
        ident = escritorio.post("/api/raphi/archivos", files=[("archivos", ("x.pdf", a))]).json()[0]["id"]
    t = esperar(escritorio, escritorio.post("/api/raphi/trabajos", json={"operacion": "receta:mia",
                                                                          "archivos": [ident]}).json()["id"])
    assert t["estado"] == "hecho" and t["salidas"][0]["nombre"] == "x_mia.pdf"
    assert escritorio.delete("/api/raphi/recetas/mia").status_code == 200
    assert escritorio.delete("/api/raphi/recetas/para-enviar").status_code == 404     # las de serie no se borran


def test_cancelar(escritorio, corpus):
    with open(corpus["largo"], "rb") as a:
        ident = escritorio.post("/api/raphi/archivos", files=[("archivos", ("largo.pdf", a))]).json()[0]["id"]
    t = escritorio.post("/api/raphi/trabajos", json={"operacion": "pdf_a_imagen", "archivos": [ident],
                                                     "params": {"ppp": 300}}).json()
    escritorio.post(f"/api/raphi/trabajos/{t['id']}/cancelar")
    assert esperar(escritorio, t["id"])["estado"] == "cancelado"


def test_purga_borra_lo_vencido_y_nunca_lo_local(entorno, corpus):
    import asyncio
    import datetime as dt
    import shutil
    from raphi import config as configuracion
    from raphi import db, trabajos
    cfg = configuracion.recargar()

    async def probar():
        await db.preparar(cfg.database_url)
        subido = cfg.subidos / "a1"
        subido.mkdir(parents=True)
        shutil.copy(corpus["texto"], subido / "x.pdf")
        salida = cfg.trabajos / "t1"
        salida.mkdir(parents=True)
        (salida / "y.pdf").write_bytes(b"%PDF")
        viejo = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=3)
        async with db.sesion() as s:
            await s.execute(db.ARCHIVOS.insert().values(id="a1", cuenta=1, nombre="x.pdf", ruta=str(subido / "x.pdf"),
                                                        bytes=1, local=False, creado_en=viejo))
            await s.execute(db.ARCHIVOS.insert().values(id="a2", cuenta=1, nombre="mio.pdf", ruta=str(corpus["texto"]),
                                                        bytes=1, local=True, creado_en=viejo))
            await s.execute(db.TRABAJOS.insert().values(id="t1", cuenta=1, operacion="rotar", estado="hecho",
                                                        terminado_en=viejo, creado_en=viejo))
            await s.commit()
        assert await trabajos.purgar() == 2
        assert not subido.exists() and not salida.exists() and corpus["texto"].is_file()
        await db.cerrar()
    asyncio.run(probar())


def test_simular_por_la_api(escritorio, corpus):
    with open(corpus["texto"], "rb") as a:
        ident = escritorio.post("/api/raphi/archivos", files=[("archivos", ("x.pdf", a))]).json()[0]["id"]
    t = esperar(escritorio, escritorio.post("/api/raphi/trabajos", json={"operacion": "comprimir", "archivos": [ident],
                                                                          "simular": True}).json()["id"])
    assert t["estado"] == "hecho" and not t["salidas"] and t["informe"]["elementos"][0]["plan"]


def test_fuera_del_escritorio_no_hay_disco(entorno, monkeypatch):
    import asyncio
    monkeypatch.setenv("JWT_SECRET", "s" * 40)
    monkeypatch.setenv("RAPHI_MODO", "sola")
    from raphi import config as configuracion
    from raphi import db
    configuracion.recargar()
    from tiqsi.minimo import Cuentas, crear_app
    from raphi.manifiesto import MANIFIESTO
    cuentas = entorno / "cuentas.json"
    Cuentas(cuentas).crear("ana", "clave-larga-123", rol="administrador", nombre="Ana")
    app = crear_app([MANIFIESTO], nombre="Raphi", secreto="s" * 40, cuentas=cuentas)
    with TestClient(app) as c:
        token = c.post("/api/auth/login", json={"usuario": "ana", "clave": "clave-larga-123"}).json()["token"]
        c.headers["Authorization"] = f"Bearer {token}"
        assert c.get("/api/raphi/operaciones").json()["modo"] == "sola"
        assert c.post("/api/raphi/locales", json={"rutas": ["/etc/hostname"]}).status_code == 403
        assert c.post("/api/raphi/trabajos", json={"operacion": "rotar", "destino": "junto"}).status_code == 403
        # La caché de docflow solo la limpia un administrador.
        Cuentas(cuentas).crear("beto", "clave-larga-456", rol="asesor", nombre="Beto")
        otro = c.post("/api/auth/login", json={"usuario": "beto", "clave": "clave-larga-456"}).json()["token"]
        assert c.post("/api/raphi/sistema/docflow/cache", json={}, headers={"Authorization": f"Bearer {otro}"}).status_code == 403
    asyncio.run(db.cerrar())


def test_capacidad_pdf_v1(corpus, tmp_path):
    import asyncio
    from raphi.contrato import CONVERSION_V1, PDF_V1

    async def probar():
        informe = await PDF_V1.ejecutar("foliar", [corpus["texto"]], {"inicio": 3}, destino=tmp_path)
        assert informe["ok"]
        assert (await PDF_V1.info(corpus["texto"]))["paginas"] == 3
        assert (await PDF_V1.miniatura(corpus["texto"], 1, 100)).startswith(b"\x89PNG")
        assert "acción" in await PDF_V1.texto(corpus["texto"])
        assert await PDF_V1.verificar_firmas(corpus["texto"]) == []
        hecho = await CONVERSION_V1.convertir(corpus["jpg"], "png", destino=tmp_path)
        assert hecho["ok"]
    asyncio.run(probar())
    with pytest.raises(AttributeError):
        PDF_V1.borrar_todo                                         # lo que no está en la superficie no existe
