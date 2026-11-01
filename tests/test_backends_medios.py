"""tests/test_backends_medios.py — los backends de medios (llegados de scripts-linux el 2026-10-31), en simulación.

Cada uno corre sobre un HOME y una carpeta de trabajo temporales; se compara un listado con tamaño y mtime de lo
temporal y del repo antes y después: una simulación no crea, modifica ni borra nada. Lo que necesita red (yt-dlp con
una URL) o datos del usuario (la base de digiKam) se prueba solo con --help o se salta con su motivo. Vino de
scripts-linux/tests/test_simulacion.py (ola 4, L1b).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
BACKENDS = REPO / "backends"

# Carpetas que no forman parte del contenido que una suite podría tocar: el propio git y los
# cachés que crea pytest al importar este archivo.
IGNORAR = {".git", ".pytest_cache"}


def instantanea(raiz: Path) -> dict[str, tuple[int, int, str]]:
    """{ruta relativa: (tamaño, mtime_ns, tipo)} de todo lo que cuelga de ``raiz`` (sin seguir enlaces)."""
    foto: dict[str, tuple[int, int, str]] = {}
    for dirpath, dirnames, filenames in os.walk(raiz, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in IGNORAR]
        for nombre in dirnames + filenames:
            p = Path(dirpath) / nombre
            st = p.lstat()
            tipo = "l" if p.is_symlink() else ("d" if p.is_dir() else "f")
            # el mtime de una carpeta cambia si se crea o borra algo dentro: también cuenta
            foto[str(p.relative_to(raiz))] = (0 if tipo == "d" else st.st_size, st.st_mtime_ns, tipo)
    return foto


def diferencias(antes: dict, despues: dict) -> list[str]:
    nuevas = sorted(set(despues) - set(antes))
    borradas = sorted(set(antes) - set(despues))
    cambiadas = sorted(k for k in set(antes) & set(despues) if antes[k] != despues[k])
    return [f"+ {k}" for k in nuevas] + [f"- {k}" for k in borradas] + [f"~ {k}" for k in cambiadas]


@pytest.fixture
def entorno(tmp_path: Path):
    """HOME, XDG_* y carpeta de trabajo temporales; devuelve (home, trabajo, env)."""
    home = tmp_path / "home"
    trabajo = tmp_path / "trabajo"
    for d in (home, trabajo, home / ".config", home / ".cache", home / ".local" / "share", home / ".local" / "state"):
        d.mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("LOG_FILE", "SGDP_USB", "GITHUB_TOKEN"))}
    env.update({
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_CACHE_HOME": str(home / ".cache"),
        "XDG_DATA_HOME": str(home / ".local" / "share"),
        "XDG_STATE_HOME": str(home / ".local" / "state"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "TERM": env.get("TERM") or "dumb",
        "NO_COLOR": "1",
        "LC_ALL": "C.UTF-8",
    })
    return home, trabajo, env


def correr_sin_escribir(cmd: list[str], raiz_tmp: Path, cwd: Path, env: dict, *, rc_esperado=(0,), entrada="",
                        timeout=120) -> subprocess.CompletedProcess:
    """Corre ``cmd`` y falla si cambió algo en ``raiz_tmp`` o en el repo, o si el código de salida no es el esperado."""
    antes_tmp, antes_repo = instantanea(raiz_tmp), instantanea(REPO)
    r = subprocess.run(cmd, cwd=cwd, env=env, input=entrada, capture_output=True, text=True, timeout=timeout)
    salida = f"\n--- stdout ---\n{r.stdout[-3000:]}\n--- stderr ---\n{r.stderr[-3000:]}"
    cambios = diferencias(antes_tmp, instantanea(raiz_tmp)) + [f"repo: {c}" for c in diferencias(antes_repo, instantanea(REPO))]
    assert not cambios, "la simulación escribió:\n" + "\n".join(cambios) + salida
    assert r.returncode in rc_esperado, f"código de salida {r.returncode}{salida}"
    return r


def requiere(*binarios: str):
    falta = [b for b in binarios if shutil.which(b) is None]
    return pytest.mark.skipif(bool(falta), reason=f"falta en PATH: {', '.join(falta)}")


def requiere_modulos(*modulos: str):
    import importlib.util
    falta = [m for m in modulos if importlib.util.find_spec(m) is None]
    return pytest.mark.skipif(bool(falta), reason=f"faltan módulos de Python: {', '.join(falta)}")


PY = sys.executable


def test_whisper_transcriber_dry_run(entorno):
    home, trabajo, env = entorno
    (trabajo / "entrevista.mp3").write_bytes(b"ID3" + b"\0" * 60)
    correr_sin_escribir([PY, str(BACKENDS / "whisper-transcriber" / "main.py"), "entrevista.mp3",
                         "-l", "es", "-m", "tiny", "--dry-run"], home.parent, trabajo, env)


def test_video_downloader_help(entorno):
    """La simulación (``--simulate <url>``) consulta la red con yt-dlp: aquí solo ``--help``."""
    home, trabajo, env = entorno
    correr_sin_escribir(["bash", str(BACKENDS / "video-downloader" / "main.sh"), "--help"],
                        home.parent, trabajo, env)


@pytest.mark.skip(reason="red: --simulate <url> consulta el sitio con yt-dlp; ver test_video_downloader_help")
def test_video_downloader_simulate():
    pass


@requiere("exiftool")
@requiere_modulos("PIL", "numpy")
@pytest.mark.parametrize("sub", ["apply", "undo", "fix-names", "embed-date"])
def test_photo_metadata_sin_execute(entorno, sub):
    """Los subcomandos que escriben simulan si no se les da ``--execute``."""
    home, trabajo, env = entorno
    fotos = trabajo / "fotos"
    fotos.mkdir()
    (fotos / "IMG_0001.jpg").write_bytes(b"\xff\xd8\xff\xd9")
    (fotos / "VID_0001.mp4").write_bytes(b"\0" * 32)
    (fotos / "20260101_120000.jpg").write_bytes(b"\xff\xd8\xff\xd9")
    # registro de un renombrado anterior, para que `undo` tenga algo que revertir
    (fotos / "_rename_log.csv").write_text("old,new\nTapo_0002.jpg,20260101_120000.jpg\n", encoding="utf-8")
    correr_sin_escribir([PY, str(BACKENDS / "photo-metadata" / "main.py"), sub, "fotos"],
                        home.parent, trabajo, env)


@pytest.mark.skip(reason="datos externos: sync-digikam lee la base de digiKam del usuario (aun en copia)")
def test_photo_metadata_sync_digikam():
    pass
