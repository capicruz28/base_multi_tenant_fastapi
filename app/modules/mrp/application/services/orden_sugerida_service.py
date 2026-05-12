"""Servicio aplicación mrp_orden_sugerida."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.mrp import (
    list_orden_sugerida as _list,
    get_orden_sugerida_by_id as _get,
    create_orden_sugerida as _create,
    update_orden_sugerida as _update,
    set_orden_sugerida_estado as _set_estado,
)
from app.modules.mrp.presentation.schemas import OrdenSugeridaCreate, OrdenSugeridaUpdate, OrdenSugeridaRead
from app.core.exceptions import NotFoundError, ValidationError

_ESTADOS_EDITABLES = {"sugerida"}
_TRANSICIONES_VALIDAS: dict[str, set[str]] = {
    "aprobada": {"sugerida"},
    "rechazada": {"sugerida", "aprobada"},
    "convertida": {"aprobada"},
}

# Campos permitidos por PUT (edición limitada, no workflow)
_PUT_ALLOWED_FIELDS = {
    "proveedor_sugerido_id",
    "lead_time_dias",
    "fecha_orden_sugerida",
    "observaciones",
}


def _normalizar_estado(estado: Optional[str]) -> str:
    return (estado or "sugerida").strip().lower()


def _validar_transicion(estado_actual: str, nuevo_estado: str) -> None:
    estado_actual_n = _normalizar_estado(estado_actual)
    nuevo_estado_n = _normalizar_estado(nuevo_estado)
    allowed_prev = _TRANSICIONES_VALIDAS.get(nuevo_estado_n)
    if not allowed_prev:
        raise ValidationError(detail=f"Transición no soportada hacia estado '{nuevo_estado_n}'")
    if estado_actual_n not in allowed_prev:
        raise ValidationError(
            detail=f"No se puede pasar de '{estado_actual_n}' a '{nuevo_estado_n}'",
            internal_code="INVALID_STATE_TRANSITION",
        )


async def list_orden_sugerida(
    client_id: UUID,
    plan_maestro_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    tipo_orden: Optional[str] = None,
) -> List[OrdenSugeridaRead]:
    rows = await _list(
        client_id=client_id,
        plan_maestro_id=plan_maestro_id,
        producto_id=producto_id,
        estado=estado,
        tipo_orden=tipo_orden,
    )
    return [OrdenSugeridaRead(**r) for r in rows]


async def get_orden_sugerida_by_id(client_id: UUID, orden_sugerida_id: UUID) -> OrdenSugeridaRead:
    row = await _get(client_id, orden_sugerida_id)
    if not row:
        raise NotFoundError(f"Orden sugerida {orden_sugerida_id} no encontrada")
    return OrdenSugeridaRead(**row)


async def create_orden_sugerida(client_id: UUID, data: OrdenSugeridaCreate) -> OrdenSugeridaRead:
    # Tabla operacional/derivada: no debería crearse manualmente vía API.
    raise ValidationError(
        detail="La orden sugerida es generada por procesos MRP (controlado). Creación manual no permitida.",
        internal_code="OPERATIONAL_TABLE_CONTROLLED_WRITE",
    )
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return OrdenSugeridaRead(**row)


async def update_orden_sugerida(
    client_id: UUID, orden_sugerida_id: UUID, data: OrdenSugeridaUpdate
) -> OrdenSugeridaRead:
    actual = await _get(client_id, orden_sugerida_id)
    if not actual:
        raise NotFoundError(f"Orden sugerida {orden_sugerida_id} no encontrada")

    estado_actual = _normalizar_estado(actual.get("estado"))
    if estado_actual not in _ESTADOS_EDITABLES:
        raise ValidationError(
            detail=f"La orden sugerida solo es editable en estado sugerida (estado actual: {estado_actual})",
            internal_code="ORDEN_SUGERIDA_NOT_EDITABLE",
        )

    payload = data.model_dump(exclude_none=True)
    disallowed = set(payload.keys()) - _PUT_ALLOWED_FIELDS
    if disallowed:
        raise ValidationError(
            detail=f"Edición no permitida por PUT para campos: {', '.join(sorted(disallowed))}",
            internal_code="PUT_FIELDS_NOT_ALLOWED",
        )

    row = await _update(client_id, orden_sugerida_id, payload)
    if not row:
        raise NotFoundError(f"Orden sugerida {orden_sugerida_id} no encontrada")
    return OrdenSugeridaRead(**row)


async def aprobar_orden_sugerida(client_id: UUID, orden_sugerida_id: UUID) -> OrdenSugeridaRead:
    actual = await _get(client_id, orden_sugerida_id)
    if not actual:
        raise NotFoundError(f"Orden sugerida {orden_sugerida_id} no encontrada")
    _validar_transicion(actual.get("estado"), "aprobada")
    row = await _set_estado(client_id, orden_sugerida_id, "aprobada")
    if not row:
        raise NotFoundError(f"Orden sugerida {orden_sugerida_id} no encontrada")
    return OrdenSugeridaRead(**row)


async def rechazar_orden_sugerida(client_id: UUID, orden_sugerida_id: UUID) -> OrdenSugeridaRead:
    actual = await _get(client_id, orden_sugerida_id)
    if not actual:
        raise NotFoundError(f"Orden sugerida {orden_sugerida_id} no encontrada")
    _validar_transicion(actual.get("estado"), "rechazada")
    row = await _set_estado(client_id, orden_sugerida_id, "rechazada")
    if not row:
        raise NotFoundError(f"Orden sugerida {orden_sugerida_id} no encontrada")
    return OrdenSugeridaRead(**row)


async def convertir_orden_sugerida(
    client_id: UUID,
    orden_sugerida_id: UUID,
    *,
    documento_generado_tipo: str,
    documento_generado_id: UUID,
) -> OrdenSugeridaRead:
    actual = await _get(client_id, orden_sugerida_id)
    if not actual:
        raise NotFoundError(f"Orden sugerida {orden_sugerida_id} no encontrada")
    _validar_transicion(actual.get("estado"), "convertida")
    row = await _set_estado(
        client_id,
        orden_sugerida_id,
        "convertida",
        documento_generado_tipo=documento_generado_tipo,
        documento_generado_id=documento_generado_id,
    )
    if not row:
        raise NotFoundError(f"Orden sugerida {orden_sugerida_id} no encontrada")
    return OrdenSugeridaRead(**row)
