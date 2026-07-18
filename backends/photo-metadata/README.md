# camera-timestamp-renamer

> Renombra **fotos y videos** de cámara de seguridad según la **fecha y hora
> impresa en la imagen** (OCR de la marca), al formato `AAAAMMDD_HHMMSS`, de
> forma segura, configurable y **reversible**. En los videos se lee la marca
> del primer fotograma (la hora de inicio de la grabación).

## 📋 Tabla de Contenidos

- [Descripción](#-descripción)
- [Requisitos](#️-requisitos)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Flujo recomendado](#-flujo-recomendado)
- [Configuración](#️-configuración)
- [Arquitectura](#️-arquitectura)
- [Solución de Problemas](#-solución-de-problemas)
- [Cómo Contribuir](#-cómo-contribuir--agregar-funcionalidades)
- [Notas y Advertencias](#️-notas-y-advertencias)

## 📖 Descripción

Muchas cámaras (Tapo y similares) guardan fotos cuyo **nombre de archivo no
coincide** con el instante real de captura, pero **sí** imprimen la fecha/hora
en una esquina de la imagen. Esta herramienta lee esa marca con OCR
(`tesseract`) y renombra cada foto a `AAAAMMDD_HHMMSS.ext`.

Está pensada para reutilizarse en casos similares: puedes cambiar **dónde** se
lee la marca, los umbrales de binarización, las extensiones aceptadas y más,
sin tocar la lógica interna. Todo cambio de archivos es **simulado por
defecto** y queda **registrado para deshacerse**.

Casos de uso: normalizar carpetas de cámaras de seguridad, corregir nombres
tras exportaciones masivas, ordenar cronológicamente por nombre.

## ⚙️ Requisitos

### Sistema Operativo

- Linux o macOS (probado en Linux).

### Dependencias del sistema

- **tesseract-ocr** — motor de OCR.
  `sudo apt install tesseract-ocr`
- **ffmpeg** — extraer fotogramas de video (solo necesario si procesas videos).
  `sudo apt install ffmpeg`
- **exiftool** — escribir la fecha en metadatos (solo para el subcomando `embed-date`).
  `sudo apt install libimage-exiftool-perl`

### Dependencias de Python

- Python >= 3.9
- Pillow >= 9.1 — recorte y montajes.
- numpy >= 1.21 — binarización vectorizada.

## 🚀 Instalación

### Paso 1: Ir a la carpeta del proyecto

```bash
cd /home/achalmaedison/Documents/scripts_for_linux/camera-timestamp-renamer
```

### Paso 2: Instalar dependencias

```bash
sudo apt install tesseract-ocr ffmpeg   # dependencias del sistema (ffmpeg: videos)
pip install -r requirements.txt         # dependencias de Python
```

## 💻 Uso

### Sintaxis

```bash
python main.py <subcomando> <carpeta> [OPCIONES]
```

### Subcomandos

| Subcomando | Qué hace | ¿Modifica archivos? |
| --- | --- | --- |
| `analyze` | Lee las marcas y escribe el plan (`rename_plan.csv`) y `analysis.json` | No |
| `verify`  | Genera montajes PNG con las lecturas dudosas y las colisiones | No |
| `apply`   | Renombra según el plan (**simula** salvo `--execute`) | Solo con `--execute` |
| `undo`    | Revierte el último renombrado usando `_rename_log.csv` | Solo con `--execute` |
| `embed-date` | Escribe la fecha de captura (EXIF/QuickTime + mtime) desde el nombre | Solo con `--execute` |

### Opciones

| Flag | Descripción | Aplica a |
| --- | --- | --- |
| `--execute` | Aplica de verdad (sin esto, solo simula) | `apply`, `undo` |
| `--from-plan FILE` | Usa un CSV de plan editado a mano | `apply`, `verify` |
| `--crop-left / --crop-top / --crop-width / --crop-height` | Posición y tamaño del recorte de análisis (fracciones 0–1) | `analyze`, `apply`, `verify` |
| `--workers N` | Procesos en paralelo (0 = todos los núcleos) | todos menos `undo` |
| `--limit N` | Procesar solo las primeras N imágenes (pruebas rápidas) | todos menos `undo` |
| `--verbose, -v` | Salida detallada | todos |
| `--log-file FILE` | Guardar los logs también en un archivo | todos |
| `--version` | Mostrar versión | — |
| `--help, -h` | Mostrar ayuda | — |

### Ejemplos

```bash
# Analizar sin tocar nada
python main.py analyze ./fotos

# Simular el renombrado (por defecto NO cambia nada)
python main.py apply ./fotos

# Aplicar de verdad (deja _rename_log.csv y _undo_rename.sh)
python main.py apply ./fotos --execute

# Deshacer
python main.py undo ./fotos --execute

# Escribir la fecha en los metadatos desde el nombre (arregla el agrupado en digiKam)
python main.py embed-date ./fotos --execute

# La marca está en OTRA posición (franja superior completa, más alta):
python main.py analyze ./fotos --crop-left 0 --crop-width 1 --crop-height 0.10
```

## 🔄 Flujo recomendado

1. **`analyze`** → revisa `rename_plan.csv` y el resumen.
2. **`verify`** → abre los `verify_review_*.png` para comprobar visualmente las
   lecturas marcadas `weak`/`dark`/`fail` y las colisiones.
3. Si algo se leyó mal, **edita la columna `new` de `rename_plan.csv`** a mano.
4. **`apply --from-plan rename_plan.csv --execute`** → aplica tu plan revisado.
5. ¿Algo no cuadró? **`undo --execute`**.

## 🎛️ Configuración

Todos los valores por defecto viven en [`config.py`](config.py) (clase
`Settings`). Los más útiles:

| Campo | Para qué | Default |
| --- | --- | --- |
| `crop_*_frac` | **Dónde** se lee la marca (posición/tamaño del recorte) | esquina sup. izq. |
| `bright_thresholds` / `dark_thresholds` | Umbrales de binarización para el OCR | listas por defecto |
| `tesseract_psms` / `tesseract_whitelist` | Modo de página y caracteres permitidos | `[7, 6]` / dígitos |
| `timestamp_regex` | Patrón de la fecha/hora en el texto OCR | `AAAA-MM-DD HH:MM:SS` |
| `year_min` / `year_max` | Rango válido de años (descarta lecturas absurdas) | 2015–2035 |
| `image_extensions` | Qué archivos se consideran fotos | `.jpg .jpeg .png` |
| `video_extensions` | Qué archivos se consideran videos | `.mp4 .mov .avi .mkv` |
| `ffmpeg_frame_times` | Segundos a probar para sacar el fotograma del video | `["0","1","2"]` |
| `image_date_tags` / `video_date_tags` | Qué etiquetas de fecha escribe `embed-date` | EXIF / QuickTime+XMP |
| `set_file_modify_date` | Fijar también el `mtime` desde el nombre (respaldo M2TS) | `True` |
| `confident_min_votes` | Votos para marcar una lectura como fiable | 3 |

Regla: los valores ajustables van en `config.py`; nunca se codifican dentro de
`lib/`.

## 🗂️ Arquitectura

```
camera-timestamp-renamer/
├── main.py              # Punto de entrada: parsea, enruta, mapea errores a códigos
├── config.py            # Configuración central (Settings) + códigos de salida
├── requirements.txt
├── README.md
└── lib/
    ├── logger.py        # Logging centralizado (INFO/WARN/ERROR)
    ├── errors.py        # Excepciones propias (DependencyError, PlanError)
    ├── validator.py     # Valida dependencias, carpeta y parámetros de recorte
    ├── cli.py           # argparse: subcomandos y overrides de configuración
    ├── ocr.py           # NÚCLEO: recorte + binarización + tesseract + votación
    ├── video.py         # Extrae un fotograma del video con ffmpeg
    ├── media.py         # Despacha foto/video hacia el mismo OCR
    ├── metadata.py      # Escribe fechas EXIF/QuickTime/mtime con exiftool
    ├── scanner.py       # Escaneo paralelo con progreso (fix OMP_THREAD_LIMIT)
    ├── planner.py       # Construye el plan y resuelve colisiones (_2, _3…)
    ├── renamer.py       # Renombrado en dos fases + log + script de deshacer
    ├── montage.py       # Montajes PNG de verificación
    └── commands.py      # Orquestación de cada subcomando
```

### Responsabilidad por módulo

| Archivo | Responsabilidad |
| --- | --- |
| `main.py` | Único punto de arranque; traduce excepciones a códigos de salida |
| `config.py` | Todo valor editable y los códigos de salida |
| `lib/ocr.py` | Leer la marca de una imagen (recorte, umbrales, votación) |
| `lib/video.py` | Extraer un fotograma de un video con ffmpeg |
| `lib/media.py` | Unificar fotos y videos sobre el mismo OCR |
| `lib/metadata.py` | Escribir la fecha en metadatos (exiftool) desde el nombre |
| `lib/scanner.py` | Recorrer la carpeta en paralelo |
| `lib/planner.py` | Decidir el nombre destino y manejar duplicados |
| `lib/renamer.py` | Aplicar/deshacer renombrados sin pérdida de datos |
| `lib/montage.py` | Generar imágenes de revisión humana |
| `lib/commands.py` | Encadenar los pasos de cada subcomando |

### Códigos de salida

| Código | Significado |
| --- | --- |
| 0 | Éxito |
| 1 | Error general (E/S) |
| 2 | Error de argumentos / plan inválido |
| 3 | Carpeta o archivo no encontrado |
| 4 | Sin permisos |
| 5 | Dependencia no instalada (tesseract) |

## 🔧 Solución de Problemas

### `'tesseract' no está instalado`

```bash
sudo apt install tesseract-ocr
```

### `ModuleNotFoundError: No module named 'PIL'` / `numpy`

```bash
pip install -r requirements.txt
```

### `'ffmpeg' no está instalado` (al procesar videos)

```bash
sudo apt install ffmpeg
```

### El OCR lee mal o no encuentra la marca

- La marca puede estar en otra posición → ajusta `--crop-*`.
- Fotos verticales con barras negras: la marca está más abajo; sube
  `--crop-top` o amplía `--crop-height`.
- Revisa con `verify` y corrige a mano el `rename_plan.csv` antes de `apply`.

### El escaneo va muy lento

Ya se aplica `OMP_THREAD_LIMIT=1` para que `tesseract` no sature los núcleos.
Ajusta `--workers` al número de núcleos físicos si hace falta.

## 🤝 Cómo Contribuir / Agregar Funcionalidades

### Para agregar un nuevo módulo de dominio

1. Crea `lib/nuevo_modulo.py` con funciones de responsabilidad única.
2. Añade sus valores ajustables a `config.py` (nunca hardcodeados en `lib/`).
3. Orquéstalo desde `lib/commands.py`.
4. Agrega las flags necesarias en `lib/cli.py`.
5. Actualiza este README.

### Estándares de código

- Máximo 30 líneas por función; propósito único.
- Nombres descriptivos en inglés (`verbo + sustantivo`).
- Type hints en firmas públicas; docstrings que documentan el contrato.
- Comenta el "por qué", no el "qué".
- `ruff check .` y `python -m py_compile` sin advertencias antes de un PR.

## ⚠️ Notas y Advertencias

- **Formato de marca soportado**: `AAAA-MM-DD HH:MM:SS` (el de cámaras Tapo).
  Para otros formatos, ajusta `timestamp_regex` en `config.py`.
- **Duplicados**: cuando dos fotos comparten fecha/hora exacta (ráfagas o
  copias) no pueden tener el mismo nombre; la segunda y siguientes reciben
  sufijo `_2`, `_3`… Es la única desviación del formato puro y garantiza que
  **no se pierda ninguna foto**.
- **Fotos sin marca** (p. ej. una imagen que no es de la cámara) se marcan
  `SKIP` y **no se tocan**.
- **Videos**: se procesan igual que las fotos, leyendo la marca del primer
  fotograma legible (la hora de inicio de la grabación). Requiere `ffmpeg`.
  Ajusta `video_extensions` y `ffmpeg_frame_times` en `config.py` si hace falta.
- **Reversibilidad**: `apply --execute` deja `_rename_log.csv` y
  `_undo_rename.sh` en la carpeta. `undo --execute` revierte y borra el log.
  Cada nuevo `apply` sobrescribe el log anterior: deshaz antes de re-aplicar.
- **Seguridad**: el renombrado es en dos fases y nunca sobrescribe un archivo
  existente; ante cualquier conflicto, aborta sin modificar nada.
- **`embed-date` y digiKam**: si tus fotos/videos aparecen agrupados por una
  fecha equivocada (p.ej. el año en que los copiaste), suele ser porque no
  tienen fecha de captura embebida y el visor usa una fecha del sistema de
  archivos. `embed-date` escribe `DateTimeOriginal` (fotos), las fechas
  QuickTime+XMP (videos) y el `mtime`, todo desde el nombre. Luego, en digiKam:
  seleccionar todo → **"Volver a leer metadatos"**.
- **Videos M2TS**: algunos `.mp4` son en realidad streams M2TS que no admiten
  metadatos embebidos; para ellos `embed-date` deja al menos el `mtime`
  correcto (por eso `set_file_modify_date` viene activado).
```
