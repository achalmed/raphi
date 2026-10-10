---
tipo: readme
estado: activo
---
# page-counter/ — cuenta las páginas de los index.pdf renderizados por cada blog Quarto y produce un reporte Excel

<!-- suite:inicio -->
**Suite `page_counter`** · objetivo *documentos* · estado *activo* · python · interfaz cli

Cuenta las páginas de los index.pdf generados por cada blog (APA) y produce un reporte por blog.

- Escribe en: archivos · simula por defecto: no
- Entrada: 04 index/_site y _pubs/*/_site
- Depende de: python3, pypdf
- Nota: cada corrida escribe su reporte Excel en excel_databases/ de la propia suite (-o le da nombre); no escribe fuera de su carpeta.

Comandos:

```bash
main.py
main.py -b <blog> [<blog> ...]
```

<sub>Bloque generado desde `suite.yml` por `core/suites.py generar` (2026-10-04); no se edita a mano.</sub>
<!-- suite:fin -->

## Qué es

Recorre los `_site/` renderizados de la familia de blogs Quarto, cuenta las páginas de cada `index.pdf`
(los PDF APA que genera apaquarto) —o de todos los PDF con `--todos`— con `pypdf`, y escribe un Excel en
su carpeta `excel_databases/` con dos hojas: «Conteo de Páginas» (bloques por blog con cada archivo, sus
páginas y su estado `OK`, `VACÍO` o `ERROR`, subtotales y total general) e «Información» (fecha, tipo de
búsqueda, totales).

Los blogs se piden por su nombre lógico, sin `pub_`: `actus-mercator`, `aequilibria`, `axiomata`, `chaska`,
`dialectica-y-mercado`, `epsilon-y-beta`, `methodica`, `numerus-scriptum`, `optimums`, `pecunia-fluxus` y
`res-publica` viven en `web/_pubs/<nombre>/_site/`; `blog` y `teching` son secciones del `_site/`
del hub (`web`), y el alias `website-achalma` selecciona las dos. La lista está en `BLOGS_ESTANDAR` de
`config.py`; la ubicación de los blogs la fija el hub (`web/docs/pubs-submodulos.md`).

## Uso

Dependencias: `pypdf` y `openpyxl`, ya incluidas en el `.venv` del repo (`install.sh` de la raíz). Desde la
raíz del repo:

```bash
python3 backends/page-counter/main.py --listar        # qué blogs están renderizados y disponibles
python3 backends/page-counter/main.py                 # todos los blogs, solo index.pdf
python3 backends/page-counter/main.py -b actus-mercator aequilibria dialectica-y-mercado pecunia-fluxus -o economia.xlsx
python3 backends/page-counter/main.py -b axiomata epsilon-y-beta numerus-scriptum optimums -o matematicas.xlsx
python3 backends/page-counter/main.py -b website-achalma          # blog y teching del hub
python3 backends/page-counter/main.py --todos -o conteo_completo.xlsx
python3 backends/page-counter/main.py -v                          # causa de cada PDF ilegible
```

| opción | efecto |
|---|---|
| `-b, --blogs <nombre…>` | solo esos blogs; un nombre desconocido aborta con salida 2 y sugiere `--listar` |
| `-t, --todos` | todos los PDF, no solo `index.pdf` |
| `-o, --output <archivo>` | nombre del Excel, siempre dentro de `excel_databases/`; por defecto `conteo_paginas_<tipo>_<fecha>_<hora>.xlsx` |
| `-l, --listar` | lista los blogs y sale |
| `-v, --verbose` | detalle, incluida la causa de cada PDF ilegible |
| `--version` · `-h, --help` | versión; ayuda |

Códigos de salida: 0 éxito, 1 error (incluye PDF ilegibles), 2 uso, 3 ruta o blogs no encontrados, 5 falta
`pypdf`. Para un conteo periódico, una línea de `crontab` que entre en la carpeta del repo y llame al
`python` del `.venv` con `backends/page-counter/main.py -o reporte_$(date +\%Y\%m).xlsx`.

Si algo falla: «No se encontraron blogs» significa que no hay `_site/` renderizados (`quarto render` en el
blog); un Excel que no se guarda suele estar abierto en LibreOffice; un PDF en `ERROR` se explica con `-v`.

## Estructura

| archivo | qué es |
|---|---|
| `main.py` | orquesta: validar → escanear → reportar → resumen |
| `config.py` | única fuente de rutas y constantes: versión, raíz, hub, prefijo `pub_`, blogs, carpeta de salida, códigos de salida |
| `lib/cli.py` | la línea de comandos |
| `lib/validator.py` | ruta base, nombres de blog, resolución de nombre lógico → carpeta |
| `lib/scanner.py` | la única pieza que abre PDF |
| `lib/excel_report.py` | la única pieza que escribe el Excel |
| `lib/ui.py` · `lib/logger.py` | presentación en la terminal; registro (`-v` → DEBUG) |
| `requirements.txt` · `install.sh` · `suite.yml` | dependencias; instalador propio (ver Límite honesto); manifiesto de la suite |

La GUI importa estos módulos tal cual (`studio/services/pagecounter.py`). Cómo añadir un módulo:
`docs/arquitectura.md` §Cómo extender. Versiones: `CHANGELOG.md`.

## Límite honesto

- **Cuenta lo renderizado, no lo escrito**: opera sobre los PDF de `_site/`; con `freeze: true` un conteo
  viejo significa un render viejo, no un fallo.
- **Siempre escribe su Excel** en `excel_databases/` (ignorado en git), sin flag de simulación; no escribe
  fuera de su carpeta. El manifiesto declara lo contrario (`escribe_en: ninguno`, simula por defecto) y
  su bloque generado de arriba cita un `--hub` que no existe: ambos pendientes en `docs/decisiones.md`.
- **La raíz de los blogs se resuelve con `Path.home()`** en `config.py`, no con `core/env.py`: si el espacio
  de trabajo no está en `~/Documents`, hay que editar `config.py`.
- **`install.sh` de esta carpeta crea un entorno conda propio**; el camino del repo es el `.venv` de la raíz.
- `excel_databases/` no es el Excel de metadatos de los blogs, que vive en `scripts-quarto`.
- Sin pruebas automáticas; sin `pypdf` solo funcionan `--listar` y `--help`.
