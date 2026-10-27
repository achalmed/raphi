"""El motor de Raphi: todas las operaciones en un solo registro (sin web, sin base, sin interfaz).

    from raphi import motor
    motor.operaciones()                                   # las fichas, para armar formularios
    motor.ejecutar("comprimir", ["a.pdf"], {"hasta": 10}, simular=True)

Importar este paquete registra todas las operaciones de sus módulos. Añadir una es escribir su función con
`@operacion(...)` en el módulo de su familia (o en uno nuevo, importado aquí): la CLI, la API y la web la muestran solas.
"""
from __future__ import annotations

from raphi.motor.base import (REGISTRO, Cancelado, ErrorOperacion, Informe, Operacion, OperacionDesconocida,
                              Parametro, Resultado, ejecutar, obtener, operacion)
from raphi.motor import (documentos, medios, pdf_avanzado, pdf_contenido, pdf_editar, pdf_info,  # noqa: F401  registran
                         pdf_optimizar, pdf_organizar, pdf_seguridad)

__all__ = ["REGISTRO", "Cancelado", "ErrorOperacion", "Informe", "Operacion", "OperacionDesconocida", "Parametro",
           "Resultado", "ejecutar", "obtener", "operacion", "operaciones", "categorias"]


def operaciones(solo_disponibles: bool = False) -> list[dict]:
    """Las fichas de todas las operaciones, en el orden de sus categorías."""
    from raphi.motor.base import CATEGORIAS
    fichas = [op.ficha() for op in REGISTRO.values()]
    if solo_disponibles:
        fichas = [f for f in fichas if not f["faltan"]]
    return sorted(fichas, key=lambda f: CATEGORIAS.index(f["categoria"]))


def categorias() -> list[str]:
    from raphi.motor.base import CATEGORIAS
    return [c for c in CATEGORIAS if any(op.categoria == c for op in REGISTRO.values())]
