---
tipo: readme
estado: activo
---
# studio/ — Raphi escritorio (PySide6; antes DocFlow Studio), paquete Python `studio`

Frontend gráfico sobre los tres backends de `../backends/`: `docflow` (conversión documental, se invoca
por `QProcess`), `pdf-suite` (manipulación PDF, `QProcess`) y `page-counter` (conteo de páginas Quarto, se
importa directo). Está organizada por **dominios funcionales**, no por scripts de origen; cada función
existe en un solo lugar. La suite `raphi` se declara en el `suite.yml` de la raíz del repo, por
eso este README no lleva bloque generado. Se arranca con `../run.sh`, `python3 ../main.py` o
`python3 -m studio` desde la raíz.

## Dominios

| dominio | qué ofrece | backend |
|---|---|---|
| Conversión de documentos | Office/ODF/PDF/EPUB/HTML/LaTeX → Markdown · PDF · Office ↔ ODF, con lotes, paralelización, caché, dry-run y respaldo de originales | docflow |
| Gestión de PDF | organizar (unir, dividir, extraer, rotar, reordenar, eliminar), optimizar (comprimir, comparar métodos, linearizar, reparar, validar, PDF/A), seguridad (cifrar, descifrar, marca de agua, numerar), contenido (PDF ↔ imagen/texto/HTML, extraer imágenes, OCR) e información | pdf-suite (PDF/A: docflow) |
| Metadatos | ver y editar XMP y DocInfo, título desde el nombre de archivo en lote, auditoría de metadatos faltantes | pdf-suite |
| Reportes | reporte de la última sesión de conversión (html/md/csv/json) y conteo de páginas de los blogs Quarto con salida Excel | docflow + page-counter |
| Vigilancia | vigilar una carpeta y convertir al vuelo lo que aparezca | docflow watch |
| Sistema | diagnóstico unificado de dependencias, caché de conversiones, `config.toml` de docflow, rutas de backends | docflow + pdf-suite |

## Experiencia de usuario

- Navegación lateral por dominios con páginas apiladas.
- Explorador de archivos acoplable: doble clic o «Usar como entrada» envía la ruta a la página activa;
  también arrastrar y soltar.
- Consola integrada: salida en vivo de cada tarea (comando, stdout, stderr, código de salida, duración).
- Panel de tareas: estado, duración y cancelación; las tareas corren en `QProcess`/`QThread` y la interfaz
  nunca se bloquea, ni en lotes de miles de archivos.
- Visor de logs: histórico persistente en `~/.local/state/raphi/studio.log` (rotado, 3 copias).
- Configuración persistente (QSettings, ~/.config/achalma/raphi.conf; migra los del nombre anterior): geometría, última
  página, últimos directorios, rutas de backends.

## Estructura

| carpeta o archivo | qué es |
|---|---|
| `__init__.py` | nombre (`Raphi`), id (`raphi`, y el anterior `docflow-studio` para migrar), versión y organización de la app |
| `app.py` · `__main__.py` | arranque: logging rotado, `QApplication`, ventana principal, `Ctrl-C` cierra |
| `core/paths.py` | única fuente de verdad para localizar los backends (`STUDIO_ROOT/backends/…`), con override del usuario en QSettings; rutas XDG del estado y de la config TOML de docflow |
| `core/settings.py` | envoltorio de QSettings: agrupa las claves para que ninguna página invente las suyas |
| `core/tasks.py` | `ProcessTask` (QProcess), `PythonTask` (hilo) y `TaskManager` |
| `services/docflow.py` · `services/pdfsuite.py` | adaptadores GUI → línea de comandos exacta (conversión, watch, report, doctor, caché, PDF/A; todas las operaciones PDF) |
| `services/pagecounter.py` | importa `../backends/page-counter` y replica el flujo de su `main.py` emitiendo por la consola |
| `ui/main_window.py` | controlador del shell `.ui` y de los docks; la tupla `PAGINAS` registra las páginas |
| `ui/pages/` | `base.py` (`BasePage`, `ListaRutas`, `SelectorRuta`) y una página por dominio: `conversion`, `pdf`, `metadata`, `reports`, `watch`, `system` |
| `ui/widgets/` | explorador, consola, panel de tareas, visor de logs |
| `resources/ui/main_window.ui` | el shell (menús, navegación, stack), editable con `pyside6-designer`; se carga en tiempo de ejecución con `QUiLoader`, sin recompilar |

## Reglas de la arquitectura

1. **Las páginas no conocen los CLIs**: construyen sus parámetros y llaman a `services/`, que devuelve la
   línea de comandos. Un cambio de flags de un backend se corrige en un solo archivo.
2. **Los backends no se modifican**: siguen siendo utilizables desde la terminal exactamente igual que
   antes (sus instaladores, tests y CI siguen operativos).
3. **Toda operación es una `Task`**: cualquier módulo nuevo hereda consola, panel de tareas, log y
   cancelación sin escribir nada.
4. **Añadir una operación PDF** = una entrada en `OPERACIONES` (`ui/pages/pdf.py`) + una función de una
   línea en `services/pdfsuite.py`.
5. **Añadir un dominio nuevo** = una página en `ui/pages/` registrada en la tupla `PAGINAS` de
   `ui/main_window.py`.

## Límite honesto

- No hay pruebas de la GUI: se comprueba abriéndola y leyendo la consola integrada y el log.
- No simula: ejecuta el comando que muestra; la simulación es la de cada backend (`-n`).
- Sin `.venv/` (`../install.sh`) arranca con el `python3` del sistema y falla si no tiene PySide6.
- Al arrancar avisa de los backends cuya ruta no existe (`paths.missing_backends`), pero no los instala.
