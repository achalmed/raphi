# audio-converter

<!-- suite:inicio -->
**Suite `audio_converter`** · objetivo *multimedia* · estado *activo* · python · interfaz cli

Convierte por lotes audios de WhatsApp (Opus) y otros formatos a MP3 con ffmpeg.

- Escribe en: archivos · simula por defecto: no
- Depende de: ffmpeg

Comandos:

```bash
main.py <carpeta> [--dry-run]
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-09-15); no se edita a mano.</sub>
<!-- suite:fin -->

> Convierte audios de WhatsApp (`.opus`, `.ogg`, `.m4a`…) —y cualquier audio
> que ffmpeg entienda— a `.mp3` por lotes. Pieza intermedia de la cadena:
> **[script_video_downloader](../script_video_downloader)** (URL → mp3/mp4) y
> **audio-converter** (archivos locales → mp3) alimentan a
> **[script_whisper_transcriber](../script_whisper_transcriber)** (mp3 → texto).

## 📋 Tabla de Contenidos

- [Descripción](#-descripción)
- [Requisitos](#%EF%B8%8F-requisitos)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Arquitectura](#%EF%B8%8F-arquitectura)
- [La cadena completa](#-la-cadena-completa)
- [Solución de Problemas](#-solución-de-problemas)
- [Cómo Contribuir](#-cómo-contribuir--agregar-nuevas-funcionalidades)
- [Notas y Advertencias](#%EF%B8%8F-notas-y-advertencias)

## 📖 Descripción

Las notas de voz de WhatsApp se guardan en formato **Opus** (`.opus`) dentro
de un contenedor OGG; muchos reproductores y herramientas no las abren, y el
transcriptor Whisper trabaja más cómodo con `.mp3`. Esta herramienta:

- Convierte **un archivo suelto** o **carpetas enteras** (opcionalmente
  recursivas: WhatsApp organiza las notas en subcarpetas por semana).
- Acepta cualquier formato que ffmpeg decodifique; al nombrar un archivo por
  CLI no se filtra por extensión (tú mandas), pero al escanear carpetas solo
  recoge las extensiones de audio configuradas.
- Es **idempotente**: si el `.mp3` de destino ya existe, lo omite (salvo
  `--overwrite`), así puedes re-ejecutar sobre la misma carpeta sin rehacer
  trabajo.
- Conserva los metadatos del original (`-map_metadata 0`) y escribe MP3 CBR
  con LAME al bitrate elegido.

Se diseñó como **script independiente** (no como opción del descargador de
vídeo) porque descargar de la red y transcodificar archivos locales son
responsabilidades distintas: mezclarlas acoplaría yt-dlp con ffmpeg sin
motivo. Encadenar ambos es trivial (ver [La cadena completa](#-la-cadena-completa)).

## ⚙️ Requisitos

### Sistema Operativo

- Linux (probado en Linux 7.x). Debería funcionar en macOS con ffmpeg.

### Dependencias

- Python >= 3.9 (solo biblioteca estándar; sin paquetes pip)
- `ffmpeg` — **única dependencia**, de sistema; hace toda la transcodificación
  (incluye el códec `libmp3lame`)

No hay `requirements.txt` porque el código no usa librerías de terceros.

## 🚀 Instalación

```bash
cd ~/Documents/scripts_for_linux/script_audio_converter
sudo apt install ffmpeg     # si no lo tienes ya
chmod +x main.py            # opcional, para ejecutarlo directo
```

## 💻 Uso

### Sintaxis

```bash
python3 main.py [OPCIONES] ENTRADA [ENTRADA ...]
```

`ENTRADA` puede ser un archivo de audio o una carpeta (se pueden mezclar
varias).

### Opciones disponibles

| Flag | Descripción | Requerido |
| --- | --- | --- |
| `ENTRADA...` | Archivo de audio o carpeta con audios | Sí |
| `-o, --output-dir DIR` | Directorio de salida (por defecto: junto a cada origen) | No |
| `-r, --recursive` | Busca también en subcarpetas | No |
| `-b, --bitrate TASA` | Bitrate del mp3, forma `128k` (32k–320k) | No (128k) |
| `--overwrite` | Reconvierte aunque el `.mp3` ya exista | No |
| `-d, --dry-run` | Simula sin escribir nada | No |
| `-v, --verbose` | Salida detallada (DEBUG) | No |
| `--version` / `-h, --help` | Versión / ayuda | No |

### Ejemplos de uso

```bash
# Una nota de voz suelta (el .mp3 queda junto al .opus)
python3 main.py PTT-20260730-WA0001.opus

# Toda la carpeta de notas de voz, con subcarpetas, a un destino aparte
python3 main.py ~/WhatsApp/"WhatsApp Voice Notes" -r -o ~/Audios_mp3

# Varias entradas mezcladas y más calidad
python3 main.py nota.opus audios_sueltos/ --bitrate 192k

# Re-ejecutar: lo ya convertido se omite (--overwrite para rehacer)
python3 main.py ~/Audios_wa -o ~/Audios_mp3

# Simular sin escribir nada
python3 main.py ~/Audios_wa -r --dry-run
```

## 🗂️ Arquitectura

```
script_audio_converter/
├── main.py                # Punto de entrada: solo orquestación
├── config.py              # TODO valor editable: extensiones, bitrate, args de ffmpeg
└── lib/
    ├── __init__.py        # Marca lib/ como paquete
    ├── logger.py          # Logging INFO/WARN/ERROR con color y archivo opcional
    ├── validator.py       # Dependencias, entradas, bitrate, dir de salida
    ├── cli.py             # argparse: flags, ayuda y ejemplos en español
    ├── scanner.py         # Descubre audios y planifica (origen -> destino .mp3)
    └── converter.py       # Invoca ffmpeg para una conversión
```

### Descripción de módulos

| Archivo | Responsabilidad |
| --- | --- |
| `main.py` | Orquesta: parseo → logger → validación → descubrir/planificar → convertir → resumen |
| `config.py` | Extensiones de audio detectadas, bitrate por defecto y límites, args base y de códec de ffmpeg, colores, códigos de salida |
| `lib/logger.py` | Logger único a stderr, color en TTY, archivo opcional |
| `lib/validator.py` | Verifica ffmpeg, existencia/permisos de entradas, formato del bitrate y dir de salida |
| `lib/cli.py` | Define todas las flags; `--help` con ejemplos y receta de encadenado |
| `lib/scanner.py` | Expande carpetas por extensión, deduplica orígenes y evita destinos colisionantes |
| `lib/converter.py` | Construye/ejecuta el argv de ffmpeg; nunca deja un mp3 a medias |

### Códigos de salida

| Código | Significado |
| --- | --- |
| 0 | Éxito (o nada que convertir) |
| 1 | Alguna conversión falló |
| 2 | Error de argumentos / uso (p. ej. bitrate inválido) |
| 3 | Ruta de entrada no encontrada |
| 4 | Sin permisos |
| 5 | ffmpeg no instalado |

(126/127 los reserva el shell; 130 = interrumpido con Ctrl-C.)

## 🔗 La cadena completa

Las tres herramientas se complementan sin solaparse:

```
                         ┌─────────────────────────┐
  URL (YouTube, etc.) ──▶│  script_video_downloader │──▶ vídeo.mp3 / vídeo.mp4
                         └─────────────────────────┘          │
                                                              ▼
  Nota de voz WhatsApp   ┌─────────────────────────┐    ┌──────────────────────────┐
  (.opus/.ogg/.m4a)  ───▶│     audio-converter      │──▶│ script_whisper_transcriber│──▶ .txt/.srt/.vtt
                         └─────────────────────────┘    └──────────────────────────┘
```

Ejemplo real (nota de voz → texto), verificado en pruebas:

```bash
# 1) WhatsApp .opus  ->  .mp3
python3 script_audio_converter/main.py nota.opus -o /tmp/mp3

# 2) .mp3  ->  transcripción
python3 script_whisper_transcriber/main.py /tmp/mp3/nota.mp3 --model small --language es
```

## 🔧 Solución de Problemas

### Error: «Falta la dependencia 'ffmpeg'»

```bash
sudo apt install ffmpeg
```

### «Sin audios convertibles en '…'»

La carpeta no tiene archivos con una extensión de la lista, o están en
subcarpetas: añade `-r`. La lista de extensiones se edita en `config.py`
(`AUDIO_EXTENSIONS`).

### ffmpeg falla con un archivo concreto

El archivo puede estar corrupto o incompleto (descarga interrumpida). El
resumen indica cuántos fallaron; usa `-v` para ver el error exacto de ffmpeg.
El `.mp3` a medias se borra automáticamente.

### La conversión pierde calidad

Sube el bitrate: `--bitrate 192k` (o edita `DEFAULT_BITRATE`). Para voz,
`128k` es más que suficiente.

## 🤝 Cómo Contribuir / Agregar Nuevas Funcionalidades

### Para agregar un nuevo módulo:

1. Crea `lib/nuevo_modulo.py` con funciones de responsabilidad única.
2. Añade sus valores ajustables en `config.py` (nunca hardcodeados en `lib/`).
3. Impórtalo y orquéstalo desde `main.py`.
4. Agrega las flags necesarias en `lib/cli.py` y valida en `lib/validator.py`.
5. Actualiza este README.

### Estándares de código

- Máximo ~30 líneas por función; nombres verbo+sustantivo en inglés.
- Docstrings/comentarios en inglés técnico; TODA salida al usuario en español.
- Comenta el «por qué», no el «qué».
- `python3 -m py_compile` y `ruff check .` limpios; prueba también los
  caminos de error (códigos de salida).

## ⚠️ Notas y Advertencias

- **Formato de salida fijo: MP3.** Es lo que pide el flujo (WhatsApp →
  transcripción). Si algún día necesitas otro contenedor, se añadiría una
  flag `--format` en `config.py`/`lib/cli.py`; hoy no se implementa para no
  inventar alcance.
- **Los `.mp3` de entrada se omiten** (ya están en el formato destino).
- **Destinos colisionantes**: si con un `--output-dir` común dos orígenes
  distintos (`a.opus` y `a.ogg`) apuntan al mismo `a.mp3`, se convierte el
  primero y se avisa del resto; ejecuta sin `-o` (salida junto al origen)
  para conservarlos separados.
- **Idempotencia**: por defecto no se rehace lo ya convertido; usa
  `--overwrite` para forzar.
- **Los archivos de origen nunca se modifican ni se borran** (a diferencia
  del notebook original de Whisper, que borraba audios): esta herramienta
  solo crea `.mp3` nuevos.
- Supuesto de diseño («hazlo directo»): se creó como script independiente en
  vez de ampliar `script_video_downloader`, por separación de
  responsabilidades (red vs. transcodificación local).
