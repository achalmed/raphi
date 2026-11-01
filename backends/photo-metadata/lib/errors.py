"""Excepciones propias del proyecto.

Permiten distinguir fallos esperables (dependencia ausente, plan inválido)
de errores genéricos y así mapearlos a códigos de salida concretos.
"""
from __future__ import annotations


class DependencyError(RuntimeError):
    """Una dependencia externa requerida no está disponible."""


class PlanError(ValueError):
    """El plan de renombrado es inconsistente o inseguro de aplicar."""
