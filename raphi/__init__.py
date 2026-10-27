"""Raphi: PDF, ofimática y conversión de archivos (escritorio, web y módulo de la plataforma Qillqa).

El paquete `raphi` tiene tres capas que no se mezclan:

- `raphi.motor`: las operaciones (Python puro, sin web ni base): cada una se declara una vez en el registro y de esa
  declaración salen la CLI, la API y los formularios de la web;
- `raphi.api`, `raphi.manifiesto`, `raphi.sola`, `raphi.escritorio`: la API FastAPI, el módulo de Tiqsi y sus modos;
- `web/` y `escritorio/` (fuera del paquete): la única interfaz y la ventana que la muestra.

Plan: `qillqa/docs/plataforma/propuesta-raphi.md` en el espacio de trabajo.
"""

VERSION = "0.1.0"
