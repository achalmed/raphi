"""Raphi Studio corre el motor en su propio proceso, sin el servidor local de la ventana web.

- `ejecutar_operacion` y `ejecutar_receta`: lo que corre un `FunctionWorker` de gui_comun (en otro hilo), con el
  avance y la cancelación del motor traducidos a los del worker;
- `MotorLocal`: lo que `escritorio/vigilancia.py` le pide al «servidor» (`pedir(ruta, datos)`), resuelto aquí mismo,
  así las carpetas vigiladas funcionan igual en el Studio que en la ventana web.
"""
from __future__ import annotations

from pathlib import Path

from gui_comun.workers.function_worker import FunctionWorker, OperationCancelled

from raphi import motor, recetas


def _puente(progress_cb, cancel_cb):
    def progreso(fraccion: float, mensaje: str) -> None:
        progress_cb(int(fraccion * 100), mensaje)
    return progreso, cancel_cb


def ejecutar_operacion(id: str, entradas: list[str], params: dict, destino: str | None, simular: bool, *,
                       progress_cb, cancel_cb, message_cb):
    progreso, cancelado = _puente(progress_cb, cancel_cb)
    informe = motor.ejecutar(id, entradas, params, destino=destino, simular=simular, progreso=progreso,
                             cancelado=cancelado)
    if cancel_cb():
        raise OperationCancelled()
    for e in informe.elementos:
        message_cb("ok" if e.ok else "error", f"{Path(e.entrada).name}: {'listo' if e.ok else e.error}")
    return informe


def ejecutar_receta(id: str, entradas: list[str], destino: str | None, simular: bool, *,
                    progress_cb, cancel_cb, message_cb):
    progreso, cancelado = _puente(progress_cb, cancel_cb)
    informe = recetas.aplicar(recetas.buscar(id), entradas, destino=destino, simular=simular, progreso=progreso,
                              cancelado=cancelado)
    for e in informe.elementos:
        message_cb("ok" if e.ok else "error", f"{Path(e.entrada).name}: {'listo' if e.ok else e.error}")
    return informe


class MotorLocal:
    """El «servidor» que espera `Vigilancia`: las dos llamadas que hace, sin HTTP."""

    def __init__(self, ventana) -> None:
        self.ventana = ventana          # quien corre los workers (y los mantiene vivos)

    def pedir(self, ruta: str, datos: dict | None = None):
        datos = datos or {}
        if ruta == "/api/raphi/locales":
            return [{"id": r} for r in datos.get("rutas", [])]
        if ruta == "/api/raphi/trabajos":
            receta = datos["operacion"].removeprefix("receta:")
            worker = FunctionWorker(ejecutar_receta, receta, list(datos.get("archivos", [])), datos.get("destino"),
                                    False, description=f"Receta {receta}")
            self.ventana.run_function_worker(worker, f"Carpeta vigilada: {receta}")
            return {"ok": True}
        raise ValueError(f"Raphi Studio no atiende {ruta}")
