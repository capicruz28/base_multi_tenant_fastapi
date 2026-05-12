"""Servicio aplicación mps_plan_produccion."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.mps import (
    list_plan_produccion as _list,
    get_plan_produccion_by_id as _get,
    create_plan_produccion as _create,
    update_plan_produccion as _update,
    set_plan_produccion_estado as _set_estado,
)
from app.modules.mps.presentation.schemas import PlanProduccionCreate, PlanProduccionUpdate, PlanProduccionRead
from app.core.exceptions import NotFoundError, ValidationError

_ESTADOS_EDITABLES = {"borrador"}

_TRANSICIONES_VALIDAS: dict[str, set[str]] = {
    "aprobado": {"borrador"},
    "ejecutado": {"aprobado"},
    "cerrado": {"ejecutado"},
    # Anular permitido mientras no esté cerrado
    "anulado": {"borrador", "aprobado", "ejecutado"},
}


def _normalizar_estado(estado: Optional[str]) -> str:
    return (estado or "borrador").strip().lower()


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


async def list_plan_produccion(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    buscar: Optional[str] = None,
) -> List[PlanProduccionRead]:
    rows = await _list(client_id=client_id, empresa_id=empresa_id, estado=estado, buscar=buscar)
    return [PlanProduccionRead(**r) for r in rows]


async def get_plan_produccion_by_id(client_id: UUID, plan_produccion_id: UUID) -> PlanProduccionRead:
    row = await _get(client_id, plan_produccion_id)
    if not row:
        raise NotFoundError(f"Plan de producción {plan_produccion_id} no encontrado")
    return PlanProduccionRead(**row)


async def create_plan_produccion(client_id: UUID, data: PlanProduccionCreate) -> PlanProduccionRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return PlanProduccionRead(**row)


async def update_plan_produccion(
    client_id: UUID, plan_produccion_id: UUID, data: PlanProduccionUpdate
) -> PlanProduccionRead:
    actual = await _get(client_id, plan_produccion_id)
    if not actual:
        raise NotFoundError(f"Plan de producción {plan_produccion_id} no encontrado")

    estado_actual = _normalizar_estado(actual.get("estado"))
    if estado_actual not in _ESTADOS_EDITABLES:
        raise ValidationError(
            detail=f"El plan de producción solo es editable en estado borrador (estado actual: {estado_actual})",
            internal_code="MPS_PLAN_NOT_EDITABLE",
        )

    # Evitar cambios de estado por PUT; las transiciones deben ser explícitas.
    if data.estado is not None and _normalizar_estado(data.estado) != estado_actual:
        raise ValidationError(
            detail="No se permite cambiar el estado por PUT. Use las acciones de transición del plan de producción.",
            internal_code="STATE_CHANGE_NOT_ALLOWED",
        )

    row = await _update(client_id, plan_produccion_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Plan de producción {plan_produccion_id} no encontrado")
    return PlanProduccionRead(**row)


async def aprobar_plan_produccion(client_id: UUID, plan_produccion_id: UUID) -> PlanProduccionRead:
    actual = await _get(client_id, plan_produccion_id)
    if not actual:
        raise NotFoundError(f"Plan de producción {plan_produccion_id} no encontrado")
    _validar_transicion(actual.get("estado"), "aprobado")
    row = await _set_estado(client_id, plan_produccion_id, "aprobado")
    if not row:
        raise NotFoundError(f"Plan de producción {plan_produccion_id} no encontrado")
    return PlanProduccionRead(**row)


async def ejecutar_plan_produccion(client_id: UUID, plan_produccion_id: UUID) -> PlanProduccionRead:
    actual = await _get(client_id, plan_produccion_id)
    if not actual:
        raise NotFoundError(f"Plan de producción {plan_produccion_id} no encontrado")
    _validar_transicion(actual.get("estado"), "ejecutado")
    row = await _set_estado(client_id, plan_produccion_id, "ejecutado")
    if not row:
        raise NotFoundError(f"Plan de producción {plan_produccion_id} no encontrado")
    return PlanProduccionRead(**row)


async def cerrar_plan_produccion(client_id: UUID, plan_produccion_id: UUID) -> PlanProduccionRead:
    actual = await _get(client_id, plan_produccion_id)
    if not actual:
        raise NotFoundError(f"Plan de producción {plan_produccion_id} no encontrado")
    _validar_transicion(actual.get("estado"), "cerrado")
    row = await _set_estado(client_id, plan_produccion_id, "cerrado")
    if not row:
        raise NotFoundError(f"Plan de producción {plan_produccion_id} no encontrado")
    return PlanProduccionRead(**row)


async def anular_plan_produccion(client_id: UUID, plan_produccion_id: UUID) -> PlanProduccionRead:
    actual = await _get(client_id, plan_produccion_id)
    if not actual:
        raise NotFoundError(f"Plan de producción {plan_produccion_id} no encontrado")
    _validar_transicion(actual.get("estado"), "anulado")
    row = await _set_estado(client_id, plan_produccion_id, "anulado")
    if not row:
        raise NotFoundError(f"Plan de producción {plan_produccion_id} no encontrado")
    return PlanProduccionRead(**row)
