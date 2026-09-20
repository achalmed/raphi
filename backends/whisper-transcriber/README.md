# whisper-transcriber

<!-- suite:inicio -->
**Suite `whisper_transcriber`** · objetivo *multimedia* · estado *activo* · python · interfaz cli

Transcribe y traduce audio o video localmente con Whisper.

- Escribe en: archivos · simula por defecto: no
- Depende de: whisper, ffmpeg

Comandos:

```bash
main.py <archivo> [--language es] [--dry-run]
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-09-20); no se edita a mano.</sub>
<!-- suite:fin -->

> Transcribe y traduce audio/video con OpenAI Whisper desde la terminal:
> acepta archivos locales, URLs de YouTube (vía yt-dlp) y subtítulos `.srt`
> para acortar. Reestructuración CLI del cuaderno Colab «Transcribir y
> Traducir OpenAI Whisper» de Jason Boog (mods. de Álex Goia).

## 📋 Tabla de Contenidos

- [Descripción](#-descripción)
- [Requisitos](#%EF%B8%8F-requisitos)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Arquitectura](#%EF%B8%8F-arquitectura)
- [Bugs Corregidos](#-bugs-corregidos)
- [Checklist de paridad funcional](#-checklist-de-paridad-funcional)
- [Solución de Problemas](#-solución-de-problemas)
- [Cómo Contribuir](#-cómo-contribuir--agregar-nuevas-funcionalidades)
- [Notas y Advertencias](#%EF%B8%8F-notas-y-advertencias)
- [Créditos y Licencia](#-créditos-y-licencia)

## 📖 Descripción

Herramienta CLI local que reproduce (y corrige) el flujo del cuaderno de
Google Colab original:

1. **Transcribir** cualquier audio o video (Whisper acepta mp3, wav, mp4,
   mkv, m4a… — ffmpeg decodifica) generando `txt`, `srt`, `vtt`, `tsv` y
   `json`.
2. **Descargar el audio de una URL** (YouTube u otro sitio compatible con
   yt-dlp) y transcribirlo directamente.
3. **Traducir al inglés** cualquier idioma (`--task translate`); las salidas
   se marcan `nombre.en.ext` para no pisar la transcripción original.
4. **Acortar subtítulos `.srt`** a líneas de ≤ N caracteres (37 por defecto,
   recomendación BBC) **sin perder texto**: se re-envuelve por palabras.

Cada tipo de entrada se detecta automáticamente: ruta local de audio/video →
transcripción; URL `http(s)://` → descarga + transcripción; archivo `.srt` →
solo acortado.

## ⚙️ Requisitos

### Sistema Operativo

- Linux (probado en Linux 7.x). Debería funcionar en macOS con los mismos
  binarios.

### Dependencias

- Python >= 3.9 (solo biblioteca estándar en el propio código)
- `openai-whisper` — motor de transcripción/traducción (provee el CLI
  `whisper`)
- `ffmpeg` — **dependencia de sistema**; Whisper lo usa para decodificar
- `yt-dlp` — solo si usas entradas URL
- `pysrt` — solo si usas `--shorten-srt` o entradas `.srt`

El validador comprueba únicamente lo que la ejecución concreta necesita: por
ejemplo, sin URLs no se exige `yt-dlp`.

## 🚀 Instalación

### Paso 1: Obtener la herramienta

```bash
cd ~/Documents/scripts_for_linux/script_whisper_transcriber
```

### Paso 2: Instalar dependencias

```bash
pip install -r requirements.txt
sudo apt install ffmpeg          # dependencia de sistema
chmod +x main.py                 # opcional, para ejecutarlo directo
```

## 💻 Uso

### Sintaxis

```bash
python3 main.py [OPCIONES] ENTRADA [ENTRADA ...]
```

`ENTRADA` puede ser un archivo de audio/video, una URL o un `.srt` (se pueden
mezclar varias en una sola llamada).

### Opciones disponibles

| Flag | Descripción | Requerido |
| --- | --- | --- |
| `ENTRADA...` | Audio/video local, URL de YouTube o subtítulo `.srt` | Sí |
| `-t, --task {transcribe,translate}` | Tarea; `translate` siempre produce inglés | No (transcribe) |
| `-m, --model MODELO` | Modelo Whisper: tiny…large, turbo | No (large) |
| `-l, --language CODIGO` | Idioma del audio (`es`, `en`…); sin él, autodetección | No |
| `--list-languages` | Lista los 100 códigos soportados y sale | No |
| `-o, --output-dir DIR` | Directorio de salidas | No (`.`) |
| `-f, --output-format FORMATO` | `txt`, `vtt`, `srt`, `tsv`, `json` o `all` | No (all) |
| `--shorten-srt` | Acorta los `.srt` generados conservando el texto | No |
| `--max-line-length N` | Longitud máxima de línea al acortar | No (37) |
| `--keep-audio` | Conserva el audio descargado de URLs | No |
| `-d, --dry-run` | Simula sin descargar/escribir nada | No |
| `-v, --verbose` | Salida detallada (DEBUG) | No |
| `--version` / `-h, --help` | Versión / ayuda | No |

### Ejemplos de uso

```bash
# Transcribir un audio local (autodetección de idioma)
python3 main.py entrevista.mp3

# Video de YouTube, idioma fijado y modelo ligero para CPU
python3 main.py "https://youtu.be/XXXXXXX" --language es --model small

# Traducir al inglés y acortar los subtítulos generados
python3 main.py charla.wav --task translate --shorten-srt

# Solo reformatear un subtítulo existente a líneas de 42 caracteres
python3 main.py pelicula.srt --max-line-length 42

# Simular todo el plan sin ejecutar nada
python3 main.py entrevista.mp3 "https://youtu.be/XXXX" --dry-run
```

Las salidas de traducción se escriben como `entrevista.en.srt`,
`entrevista.en.txt`, etc.; los subtítulos acortados como
`entrevista_acortado.srt` (el original nunca se modifica).

## 🗂️ Arquitectura

```
script_whisper_transcriber/
├── main.py                    # Punto de entrada: solo orquestación
├── config.py                  # TODO valor editable: modelos, formatos, idiomas, colores
├── requirements.txt           # Dependencias Python
└── lib/
    ├── __init__.py            # Marca lib/ como paquete
    ├── logger.py              # Logging INFO/WARN/ERROR con color y archivo opcional
    ├── validator.py           # Entradas, opciones, dependencias, códigos de salida
    ├── cli.py                 # argparse: flags, ayuda y ejemplos en español
    ├── downloader.py          # URL → mp3 con yt-dlp (sin shell, sin inyección)
    ├── transcriber.py         # Invocación de whisper + etiquetado .en de traducciones
    └── subtitle_shortener.py  # Re-envoltura de .srt por palabras (pysrt)
```

### Descripción de módulos

| Archivo | Responsabilidad |
| --- | --- |
| `main.py` | Orquesta: parseo → logger → validación → pipeline por entrada → resumen; limpieza de temporales garantizada en `finally` |
| `config.py` | Constantes editables: modelo/tarea/formato por defecto, plantilla yt-dlp, catálogo de 100 idiomas, colores ANSI, códigos de salida |
| `lib/logger.py` | Logger único a stderr (stdout queda limpio para datos), color en TTY, archivo opcional |
| `lib/validator.py` | Clasifica entradas (url/srt/media), verifica existencia/permisos y solo las dependencias que la ejecución necesita |
| `lib/cli.py` | Define todas las flags; `--help` con ejemplos reales |
| `lib/downloader.py` | Construye y ejecuta el argv de yt-dlp; localiza el mp3 producido; mueve a salidas si `--keep-audio` |
| `lib/transcriber.py` | Construye y ejecuta el argv de whisper; calcula salidas esperadas; renombra traducciones a `.en.*` |
| `lib/subtitle_shortener.py` | `wrap_subtitle_text()` puro y testeable + lectura/escritura `.srt` con pysrt |

### Códigos de salida

| Código | Significado |
| --- | --- |
| 0 | Éxito |
| 1 | Error general (falló whisper/yt-dlp en alguna entrada) |
| 2 | Error de argumentos / uso |
| 3 | Archivo no encontrado |
| 4 | Sin permisos |
| 5 | Dependencia no instalada |

(126/127 los reserva el shell; 130 = interrumpido con Ctrl-C.)

## 🐛 Bugs Corregidos

### Bug #1: Inyección/rotura de shell en las descargas

- **Descripción**: `!yt-dlp ... {LINK}` y `os.system(f"yt-dlp ... {LINK}")`
  interpolaban la URL sin comillas en una línea de shell. Una URL con `&`
  (como las de playlist del propio cuaderno) parte el comando; una URL
  maliciosa ejecuta lo que quiera.
- **Impacto**: descargas rotas o ejecución arbitraria de comandos.
- **Corrección**: `subprocess.run([...])` con lista de argumentos y sin
  shell (`lib/downloader.py`); la inyección es imposible por construcción.

### Bug #2: «¡Descarga completada!» incondicional

- **Descripción**: el mensaje de éxito se imprimía sin comprobar el código
  de retorno de yt-dlp.
- **Impacto**: fallos silenciosos; el usuario cree que tiene el audio.
- **Corrección**: se comprueba `returncode` y se verifica que el `.mp3`
  exista de verdad antes de continuar.

### Bug #3: Las URLs con `&list=` descargaban la playlist entera

- **Descripción**: los enlaces de ejemplo llevaban parámetro de playlist y
  la plantilla fija `audio.%(ext)s` hacía que cada entrada sobrescribiera a
  la anterior.
- **Impacto**: descargas eternas y archivo final impredecible.
- **Corrección**: `--no-playlist` por defecto (editable en `config.py`) y
  plantilla `%(title)s [%(id)s]` sin colisiones.

### Bug #4: El acortador de subtítulos BORRABA texto

- **Descripción**: `sub.text = sub.text[:37]` trunca cada subtítulo a sus
  primeros 37 caracteres, descartando el resto.
- **Impacto**: pérdida de contenido en todos los subtítulos largos.
- **Corrección**: re-envoltura por palabras con `textwrap` conservando el
  100 % del texto (`wrap_subtitle_text`); líneas ≤ N caracteres.

### Bug #5: Nombre de `.srt` de una versión antigua de Whisper

- **Descripción**: el acortador leía `audio.mp3.srt` (nomenclatura de
  Whisper 2022) mientras el resto del cuaderno usa la moderna `audio.srt`.
- **Impacto**: `FileNotFoundError` con cualquier Whisper actual.
- **Corrección**: se opera sobre las rutas realmente generadas en la
  ejecución, calculadas en `lib/transcriber.py`.

### Bug #6: La traducción sobrescribía la transcripción

- **Descripción**: transcribir y luego traducir escriben ambos
  `audio.txt/srt/vtt/tsv/json` en el mismo directorio.
- **Impacto**: pérdida de la transcripción en idioma original.
- **Corrección**: en `--task translate`, Whisper escribe en un directorio
  temporal y sus salidas se **mueven** ya etiquetadas `audio.en.*` (etiqueta
  configurable `TRANSLATION_TAG`). Renombrar *después* no bastaba: Whisper
  pisa el `audio.srt` en cuanto escribe, antes de poder renombrarlo — se
  detectó probando con Whisper real, no en simulación.

### Bug #7: La traducción usaba otro modelo sin avisar

- **Descripción**: la celda de traducción llamaba `whisper --task translate`
  sin `--model`, usando el modelo por defecto en lugar del `large` de la
  transcripción.
- **Impacto**: calidad inconsistente y re-descarga de otro modelo.
- **Corrección**: ambas tareas usan el mismo `--model` seleccionado.

### Bug #8: Catálogo de idiomas truncado y código hebreo inválido

- **Descripción**: el desplegable traía 47 idiomas y se cortaba en el
  coreano (faltaban portugués, ruso, chino, neerlandés, polaco, turco,
  ucraniano…); además usaba `iw` (código obsoleto de Google) para hebreo.
- **Impacto**: idiomas frecuentes inseleccionables; `--language iw` hace
  fallar a Whisper.
- **Corrección**: catálogo completo de 100 códigos en `config.py` con `he`;
  `--list-languages` los muestra y el validador rechaza códigos erróneos
  con mensaje útil.

### Bug #9: La limpieza borraba el audio del usuario

- **Descripción**: la celda de limpieza eliminaba `audio.mp3` aunque fuera
  un archivo subido por el usuario.
- **Impacto**: pérdida de datos fuera del entorno desechable de Colab.
- **Corrección**: los archivos del usuario no se tocan jamás; solo se
  limpia el directorio temporal de descargas (y `--keep-audio` lo conserva).

### Bug #10: Sin manejo de errores ni comprobación de dependencias

- **Descripción**: el cuaderno asumía whisper/ffmpeg/yt-dlp instalados y no
  trataba ningún fallo.
- **Impacto**: errores crípticos al primer problema real.
- **Corrección**: `lib/validator.py` verifica entradas, permisos y
  dependencias (con instrucción de instalación) antes de ejecutar nada, con
  códigos de salida documentados.

## ✅ Checklist de paridad funcional

| Funcionalidad original (celda del Colab) | Dónde vive ahora |
| --- | --- |
| Instalación de dependencias (`pip`/`apt`) | README + `requirements.txt`; `lib/validator.py` las verifica (exit 5) |
| Opción 1: audio de YouTube (`yt-dlp -x mp3`) | `lib/downloader.py` — entrada URL |
| Descarga del video completo (`.mp4`) | **No reimplementado** aquí (ver [Notas](#%EF%B8%8F-notas-y-advertencias)): usa `script_video_downloader` |
| Opción 2: subir tu propio `audio.mp3` | Entrada = cualquier ruta local de audio/video |
| Desplegable de idioma (ipywidgets, 47 idiomas) | `--language` + `--list-languages` (100 idiomas, `config.py`) |
| Transcribir (`whisper --model large --language X`) | `lib/transcriber.py`; `--task transcribe`, `--model` (default `large`) |
| Acortar subtítulos `.srt` (pysrt, 37 chars) | `lib/subtitle_shortener.py`; `--shorten-srt`, `--max-line-length`, entradas `.srt` directas |
| Traducir al inglés (`whisper --task translate`) | `--task translate` (mismo modelo; salidas `.en.*`) |
| Descargar archivos generados (`google.colab.files`) | No aplica en local: las salidas quedan en `--output-dir` |
| Eliminar archivos generados | Temporales autolimpiados en `finally`; `--keep-audio` conserva el audio |
| Licencia MIT y créditos | [Créditos y Licencia](#-créditos-y-licencia) |

## 🔧 Solución de Problemas

### Error: «Falta la dependencia 'whisper'»

```bash
pip install -U openai-whisper
```

### Error: «Falta la dependencia 'ffmpeg'»

```bash
sudo apt install ffmpeg
```

### La transcripción es lentísima

Estás usando `large` (el default heredado del Colab, pensado para GPU) en
CPU. Usa un modelo menor o cambia `DEFAULT_MODEL` en `config.py`:

```bash
python3 main.py audio.mp3 --model small     # o turbo, medium…
```

### Aviso `FP16 is not supported on CPU; using FP32 instead`

Es informativo (lo emite Whisper en CPU); no afecta al resultado.

### La descarga de YouTube falla

Actualiza yt-dlp (YouTube cambia a menudo): `pip install -U yt-dlp`.

## 🤝 Cómo Contribuir / Agregar Nuevas Funcionalidades

### Para agregar un nuevo módulo:

1. Crea `lib/nuevo_modulo.py` con funciones de responsabilidad única.
2. Añade sus valores ajustables en `config.py` (nunca hardcodeados en
   `lib/`).
3. Impórtalo y orquéstalo desde `main.py`.
4. Agrega las flags necesarias en `lib/cli.py` y valida en
   `lib/validator.py`.
5. Actualiza este README (tabla de opciones, arquitectura).

### Estándares de código

- Máximo ~30 líneas por función; nombres verbo+sustantivo en inglés.
- Docstrings/comentarios en inglés técnico; TODA salida al usuario en
  español.
- Comenta el «por qué», no el «qué».
- `python3 -m py_compile` y `ruff check .` limpios antes de commitear;
  prueba también los caminos de error (códigos de salida).

## ⚠️ Notas y Advertencias

- **Descarga de video completo omitida**: la celda que bajaba el `.mp4`
  entero no alimentaba a la transcripción (código muerto en el cuaderno) y
  este repo ya tiene una herramienta dedicada, `script_video_downloader`.
  Decisión documentada aquí para su aprobación; se puede añadir si la
  necesitas.
- **`--task translate` solo produce inglés**: limitación de Whisper, igual
  que en el original.
- **Modelo por defecto `large`** (paridad con el Colab): en CPU es muy
  pesado — usa `--model small`/`turbo` o edita `DEFAULT_MODEL`.
- **En `--dry-run` las dependencias ausentes son WARN, no error**, para
  poder inspeccionar el plan en máquinas sin Whisper; la ejecución real
  sale con código 5.
- **Varias entradas**: el fallo de una no detiene a las demás; al final se
  devuelve 1 si alguna falló (el resumen lo detalla).
- **Entradas `.srt`** solo se acortan (no se transcriben); el resultado va a
  `*_acortado.srt` sin tocar el original.
- Supuesto de reestructuración («hazlo directo»): celdas exclusivas de
  Colab (subida/descarga de archivos del navegador, ipywidgets) se
  sustituyeron por sus equivalentes CLI naturales, listados en la checklist
  de paridad.

## 📜 Créditos y Licencia

- Cuaderno original: [Jason Boog](https://medium.com/@jasonboog) — licencia
  MIT (2022). Modificaciones del cuaderno: Álex Goia.
- Reestructuración CLI modular: Edison Achalma (2026), misma licencia MIT.
- Motor: [OpenAI Whisper](https://github.com/openai/whisper) ·
  Descargas: [yt-dlp](https://github.com/yt-dlp/yt-dlp) ·
  Subtítulos: [pysrt](https://github.com/byroot/pysrt).
