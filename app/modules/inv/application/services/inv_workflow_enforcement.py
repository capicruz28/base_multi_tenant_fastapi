"""
Enforcement de workflow INV — estados y campos de proceso no editables por el cliente.

INV-P0-006: helpers centralizados para sanitizar CREATE y rechazar campos en UPDATE.
"""
from __future__ import annotations

from typing import Any

from app.core.exceptions import ConflictError, ValidationError

# Campos de proceso que el cliente no puede enviar en CREATE (se eliminan).
MOVIMIENTO_WORKFLOW_READONLY_CREATE: frozenset[str] = frozenset(
    {
        "autorizado_por_usuario_id",
        "fecha_autorizacion",
        "usuario_procesado_id",
        "fecha_procesado",
        "motivo_anulacion",
    }
)

# Campos de proceso + estado prohibidos en UPDATE vía API.
MOVIMIENTO_WORKFLOW_READONLY_UPDATE: frozenset[str] = frozenset(
    {"estado"} | MOVIMIENTO_WORKFLOW_READONLY_CREATE
)

INVENTARIO_FISICO_WORKFLOW_READONLY_CREATE: frozenset[str] = frozenset(
    {
        "movimiento_ajuste_id",
        "fecha_finalizacion",
        "fecha_ajuste",
        "total_productos_contados",
        "total_diferencias",
        "valor_diferencias",
    }
)

INVENTARIO_FISICO_WORKFLOW_READONLY_UPDATE: frozenset[str] = frozenset(
    {"estado"} | INVENTARIO_FISICO_WORKFLOW_READONLY_CREATE
)

_MSG_CAMPO_PROCESO = (
    "El campo '{campo}' solo se asigna mediante los endpoints de proceso del workflow."
)
_MSG_ESTADO_NO_EDITABLE = (
    "El campo 'estado' no es editable. Use los endpoints de proceso del workflow."
)
_MSG_PHANTOM_PROCESADO = (
    "Movimiento marcado como procesado sin evidencia de proceso. Estado inconsistente."
)
_MSG_PHANTOM_AUTORIZADO = (
    "Movimiento marcado como autorizado sin evidencia de autorización. Estado inconsistente."
)


def _reject_workflow_fields(
    payload: dict[str, Any],
    forbidden: frozenset[str],
) -> None:
    for campo in forbidden:
        if campo in payload:
            if campo == "estado":
                raise ValidationError(detail=_MSG_ESTADO_NO_EDITABLE)
            raise ValidationError(detail=_MSG_CAMPO_PROCESO.format(campo=campo))


def sanitize_movimiento_create_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Fuerza estado=borrador y elimina campos de proceso del payload de alta."""
    result = dict(payload)
    for campo in MOVIMIENTO_WORKFLOW_READONLY_CREATE:
        result.pop(campo, None)
    result["estado"] = "borrador"
    return result


def reject_movimiento_workflow_in_update(payload: dict[str, Any]) -> None:
    """Rechaza campos de workflow en UPDATE de movimiento."""
    _reject_workflow_fields(payload, MOVIMIENTO_WORKFLOW_READONLY_UPDATE)


def sanitize_inventario_fisico_create_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Fuerza estado=en_proceso y elimina campos de cierre del payload de alta."""
    result = dict(payload)
    for campo in INVENTARIO_FISICO_WORKFLOW_READONLY_CREATE:
        result.pop(campo, None)
    result["estado"] = "en_proceso"
    return result


def reject_inventario_fisico_workflow_in_update(payload: dict[str, Any]) -> None:
    """Rechaza campos de workflow en UPDATE de inventario físico."""
    _reject_workflow_fields(payload, INVENTARIO_FISICO_WORKFLOW_READONLY_UPDATE)


def is_phantom_procesado(mov: dict[str, Any]) -> bool:
    """True si estado=procesado sin fecha_procesado o sin usuario_procesado_id."""
    if (mov.get("estado") or "").lower() != "procesado":
        return False
    return mov.get("fecha_procesado") is None or mov.get("usuario_procesado_id") is None


def is_phantom_autorizado(mov: dict[str, Any]) -> bool:
    """True si estado=autorizado sin fecha_autorizacion o sin autorizado_por_usuario_id."""
    if (mov.get("estado") or "").lower() != "autorizado":
        return False
    return (
        mov.get("fecha_autorizacion") is None
        or mov.get("autorizado_por_usuario_id") is None
    )


def assert_movimiento_procesable(mov: dict[str, Any]) -> None:
    """409 si el movimiento está marcado procesado sin evidencia de proceso."""
    if is_phantom_procesado(mov):
        raise ConflictError(detail=_MSG_PHANTOM_PROCESADO)


def assert_movimiento_autorizable(mov: dict[str, Any]) -> None:
    """409 si el movimiento está marcado autorizado sin evidencia de autorización."""
    if is_phantom_autorizado(mov):
        raise ConflictError(detail=_MSG_PHANTOM_AUTORIZADO)
