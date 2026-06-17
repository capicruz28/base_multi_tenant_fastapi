"""
Contexto de auditoría INV — usuario de sesión en CREATE/UPDATE.

INV-P0-004: helpers para inyectar campos de auditoría usuario sin aceptar valores del body.
"""
from __future__ import annotations

from typing import Any, Optional
from uuid import UUID


def apply_create_audit(payload: dict[str, Any], usuario_id: Optional[UUID]) -> dict[str, Any]:
    """Asigna usuario_creacion_id desde sesión; ignora cualquier valor previo en el payload."""
    result = dict(payload)
    result.pop("usuario_creacion_id", None)
    result["usuario_creacion_id"] = usuario_id
    return result


def apply_producto_update_audit(
    payload: dict[str, Any],
    usuario_id: Optional[UUID],
) -> dict[str, Any]:
    """Asigna usuario_actualizacion_id solo cuando hay usuario de sesión."""
    result = dict(payload)
    result.pop("usuario_actualizacion_id", None)
    if usuario_id is not None:
        result["usuario_actualizacion_id"] = usuario_id
    return result
