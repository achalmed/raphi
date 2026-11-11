"""Archivos de cualquier tipo: qué metadatos llevan, su huella (suma de verificación), si una huella coincide y si un
comprimido está sano. Lo de KDE-Services («CheckSum Tools», «Compressed File Integrity Check») y lo de Metadata
Cleaner (ver antes de limpiar), dentro del motor: la CLI, la web, Raphi Studio y la rueda lo tienen a la vez.

- `ver_metadatos`: todo lo que exiftool lee de un archivo, por grupo (EXIF, GPS, XMP, ID3, QuickTime, PDF…), con lo
  que delata a la persona (autor, GPS, programa, número de serie) aparte; y lo que mat2 quitaría, si está.
- `suma_verificacion`: MD5, SHA-1, SHA-256 o SHA-512 (o todas), y el archivo `.sha256` al lado, como `sha256sum`.
- `verificar_suma`: lee un `.md5`/`.sha1`/`.sha256`/`.sha512` y comprueba cada archivo que nombra.
- `verificar_comprimido`: `7z t` (ZIP, 7Z, TAR, RAR…): si se puede extraer entero, sin escribir nada.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from raphi.motor.base import ErrorOperacion, Parametro, Resultado, disponible, operacion
from raphi.motor.utiles import correr

ALGORITMOS = ("md5", "sha1", "sha256", "sha512")
EXT_SUMAS = (".md5", ".sha1", ".sha256", ".sha512", ".md5sum", ".sha1sum", ".sha256sum", ".sha512sum")
COMPRIMIDOS = (".zip", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".rar", ".cbz", ".cbr", ".jar", ".apk", ".iso")
# Los grupos de exiftool que describen el archivo y no a quien lo hizo: no cuentan como «metadatos que delatan»
TECNICOS = ("ExifTool", "System", "File", "Composite")
DELATAN = re.compile(r"(author|artist|creator|owner|copyright|gps|location|serial|software|producer|make|model|"
                     r"user|comment|company|manager|lastmodifiedby|hostname|email|xmptoolkit|history|camera|lens)",
                     re.IGNORECASE)


def leer_metadatos(ruta: Path) -> dict[str, dict[str, str]]:
    """{grupo: {campo: valor}} con exiftool (-G1: el grupo fino, p. ej. «IFD0», «GPS», «XMP-dc», «ID3v2_3»)."""
    r = correr(["exiftool", "-j", "-G1", "-a", "-s", "-n", "-x", "SourceFile", str(ruta)], timeout=120,
               mensaje=f"exiftool no pudo leer {ruta.name}")
    try:
        crudo = json.loads(r.stdout or "[]")[0]
    except (ValueError, IndexError) as e:
        raise ErrorOperacion(f"exiftool no devolvió datos de {ruta.name}.") from e
    grupos: dict[str, dict[str, str]] = {}
    for clave, valor in crudo.items():
        grupo, _, campo = clave.partition(":")
        if not campo:
            grupo, campo = "Otros", clave
        texto = json.dumps(valor, ensure_ascii=False) if isinstance(valor, (dict, list)) else str(valor)
        if texto.startswith("(Binary data"):
            texto = "(datos binarios)"
        grupos.setdefault(grupo, {})[campo] = texto[:500]
    return grupos


def contar_personales(grupos: dict[str, dict[str, str]]) -> int:
    """Cuántos campos no son técnicos (los que una limpieza debe quitar)."""
    return sum(len(c) for g, c in grupos.items() if g not in TECNICOS)


@operacion("ver_metadatos", "Información", "Ver metadatos",
           "Todo lo que el archivo dice de sí y de quien lo hizo (EXIF, GPS, XMP, ID3, autor, programa, fechas), por "
           "grupo, con lo que te delata aparte y lo que mat2 quitaría. No escribe nada.",
           entrada="archivos", extensiones=(), requiere=("exiftool",),
           palabras=("exif", "metadata", "propiedades", "gps", "autor", "privacidad", "mat2", "metadata cleaner"))
def ver_metadatos(ctx):
    if ctx.simular:
        return Resultado(plan=[f"leer los metadatos de {ctx.entrada.name} (exiftool)"])
    if ctx.entrada.is_dir():
        raise ErrorOperacion(f"{ctx.entrada.name} es una carpeta: elige sus archivos.")
    grupos = leer_metadatos(ctx.entrada)
    delatan = {f"{g} › {c}": v for g, campos in grupos.items() if g not in TECNICOS for c, v in campos.items() if DELATAN.search(c)}
    datos: dict = {}
    if delatan:
        datos["Lo que te delata"] = delatan
    datos.update({g: c for g, c in grupos.items() if g not in TECNICOS})
    datos["Archivo"] = {c: v for g in TECNICOS for c, v in grupos.get(g, {}).items()
                        if c in ("FileSize", "FileType", "MIMEType", "ImageSize", "Duration", "PageCount", "FileModifyDate")}
    if disponible("mat2"):
        r = correr(["mat2", "--show", str(ctx.entrada)], timeout=120, mensaje="mat2 no pudo leerlo")
        lineas = [l.strip() for l in r.stdout.splitlines()[1:] if l.strip()]
        datos["mat2 quitaría"] = {l.split(":", 1)[0].strip(): l.split(":", 1)[1].strip() for l in lineas if ":" in l} or {"nada": "sin metadatos que mat2 sepa quitar"}
    n = contar_personales(grupos)
    return Resultado(datos=datos, mensajes=[f"{n} campos que no son técnicos; {len(delatan)} pueden identificarte"])


def _huella(ruta: Path, algoritmo: str, ctx=None) -> str:
    h = hashlib.new(algoritmo)
    total = ruta.stat().st_size or 1
    leido = 0
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(4 << 20), b""):
            h.update(bloque)
            leido += len(bloque)
            if ctx is not None:
                ctx.avisar(leido / total, algoritmo.upper())
    return h.hexdigest()


@operacion("suma_verificacion", "Archivos", "Suma de verificación",
           "La huella MD5, SHA-1, SHA-256 o SHA-512 del archivo (o todas) y, si se pide, el archivo .sha256 a su lado, "
           "como sha256sum: para comprobar después que nadie lo cambió.",
           entrada="archivos", extensiones=(), sufijo="suma",
           parametros=(Parametro("algoritmo", "Algoritmo", "opcion", "sha256",
                                 opciones=(("md5", "MD5 (rápido, no seguro)"), ("sha1", "SHA-1"), ("sha256", "SHA-256"),
                                           ("sha512", "SHA-512"), ("todas", "Todas"))),
                       Parametro("escribir", "Guardar el archivo de la suma al lado", "casilla", True)),
           palabras=("checksum", "hash", "md5", "sha256", "huella", "integridad", "sha256sum"))
def suma_verificacion(ctx):
    if ctx.entrada.is_dir():
        raise ErrorOperacion(f"{ctx.entrada.name} es una carpeta: elige sus archivos.")
    algoritmos = ALGORITMOS if ctx.p("algoritmo") == "todas" else (ctx.p("algoritmo"),)
    destinos = {a: ctx.salida(nombre=ctx.entrada.name, extension=f".{a}") for a in algoritmos} if ctx.p("escribir") else {}
    if ctx.simular:
        return Resultado(plan=[f"{', '.join(a.upper() for a in algoritmos)} de {ctx.entrada.name}"]
                         + [f"→ {d.name}" for d in destinos.values()])
    huellas = {a.upper(): _huella(ctx.entrada, a, ctx) for a in algoritmos}
    for a, destino in destinos.items():
        destino.write_text(f"{huellas[a.upper()]}  {ctx.entrada.name}\n", encoding="utf-8")
    return Resultado(list(destinos.values()), {"archivo": ctx.entrada.name, **huellas})


def _leer_sumas(ruta: Path) -> list[tuple[str, str, str]]:
    """(algoritmo, huella, nombre) de cada línea de un archivo de sumas (formato de sha256sum o BSD «SHA256 (x) = h»)."""
    largo = {32: "md5", 40: "sha1", 64: "sha256", 128: "sha512"}
    filas = []
    for linea in ruta.read_text(encoding="utf-8", errors="replace").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        bsd = re.fullmatch(r"(MD5|SHA1|SHA256|SHA512)\s*\((.+)\)\s*=\s*([0-9a-fA-F]+)", linea)
        if bsd:
            filas.append((bsd[1].lower(), bsd[3].lower(), bsd[2]))
            continue
        gnu = re.fullmatch(r"([0-9a-fA-F]{32,128})\s+\*?(.+)", linea)
        if gnu and len(gnu[1]) in largo:
            filas.append((largo[len(gnu[1])], gnu[1].lower(), gnu[2]))
    return filas


@operacion("verificar_suma", "Información", "Verificar suma",
           "Lee un archivo de sumas (.md5, .sha1, .sha256, .sha512, de sha256sum o del estilo BSD) y comprueba que cada "
           "archivo que nombra, junto a él, tenga esa huella.",
           entrada="archivos", extensiones=EXT_SUMAS,
           palabras=("checksum", "comprobar", "integridad", "descarga", "iso"))
def verificar_suma(ctx):
    filas = _leer_sumas(ctx.entrada)
    if not filas:
        raise ErrorOperacion(f"{ctx.entrada.name} no tiene ninguna suma reconocible.")
    if ctx.simular:
        return Resultado(plan=[f"comprobar {len(filas)} archivo(s) contra {ctx.entrada.name}"])
    estado: dict[str, str] = {}
    mal = 0
    for i, (algoritmo, esperado, nombre) in enumerate(filas):
        ctx.avisar(i / len(filas), nombre)
        archivo = (ctx.entrada.parent / nombre).resolve()
        if not archivo.is_file():
            estado[nombre], mal = "falta el archivo", mal + 1
        elif _huella(archivo, algoritmo) == esperado:
            estado[nombre] = f"correcto ({algoritmo.upper()})"
        else:
            estado[nombre], mal = f"NO COINCIDE ({algoritmo.upper()})", mal + 1
    if mal:
        raise ErrorOperacion(f"{mal} de {len(filas)} no coinciden o faltan: " + "; ".join(f"{k}: {v}" for k, v in estado.items() if not v.startswith("correcto")))
    return Resultado(datos=estado, mensajes=[f"{len(filas)} de {len(filas)} correctos"])


@operacion("verificar_comprimido", "Información", "Comprobar comprimido",
           "Prueba que el comprimido (ZIP, 7Z, TAR, RAR, ISO…) se pueda extraer entero, sin extraer nada: 7z t.",
           entrada="archivos", extensiones=COMPRIMIDOS, requiere=("7z",),
           parametros=(Parametro("clave", "Contraseña (si la tiene)", "clave", ""),),
           palabras=("integridad", "zip", "roto", "dañado", "corrupto", "test"))
def verificar_comprimido(ctx):
    if ctx.simular:
        return Resultado(plan=[f"7z t {ctx.entrada.name}"])
    import subprocess
    r = subprocess.run(["7z", "t", "-bd", f"-p{ctx.p('clave') or ''}", str(ctx.entrada)], capture_output=True, text=True,
                       timeout=3600)
    salida = r.stdout + r.stderr
    archivos = re.search(r"Files:\s*(\d+)", salida)
    tamano = re.search(r"Size:\s*(\d+)", salida)
    if r.returncode != 0 or "Everything is Ok" not in salida:
        errores = [l.strip() for l in salida.splitlines() if re.search(r"ERROR|Error|Wrong password|CRC Failed|Data Error", l)]
        raise ErrorOperacion(f"{ctx.entrada.name} está dañado o la contraseña no es: " + " · ".join(errores[:4] or ["7z falló"]))
    return Resultado(datos={"estado": "sano: se puede extraer entero", "archivos": archivos[1] if archivos else "1",
                            "bytes sin comprimir": tamano[1] if tamano else "—"},
                     mensajes=[f"{ctx.entrada.name}: todo bien"])
