"""Servicio aplicación mrp_necesidad_bruta."""
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from app.infrastructure.database.queries.mrp import (
    list_necesidad_bruta as _list,
    get_necesidad_bruta_by_id as _get,
    create_necesidad_bruta as _create,
    update_necesidad_bruta as _update,
    get_plan_maestro_by_id as _get_plan_maestro,
)
from app.modules.mrp.presentation.schemas import NecesidadBrutaCreate, NecesidadBrutaUpdate, NecesidadBrutaRead
from app.core.exceptions import NotFoundError, ValidationError


async def list_necesidad_bruta(
    client_id: UUID,
    plan_maestro_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    origen: Optional[str] = None,
) -> List[NecesidadBrutaRead]:
    rows = await _list(client_id=client_id, plan_maestro_id=plan_maestro_id, producto_id=producto_id, origen=origen)
    return [NecesidadBrutaRead(**r) for r in rows]


async def get_necesidad_bruta_by_id(client_id: UUID, necesidad_id: UUID) -> NecesidadBrutaRead:
    row = await _get(client_id, necesidad_id)
    if not row:
        raise NotFoundError(f"Necesidad bruta {necesidad_id} no encontrada")
    return NecesidadBrutaRead(**row)


async def create_necesidad_bruta(client_id: UUID, data: NecesidadBrutaCreate) -> NecesidadBrutaRead:
    plan = await _get_plan_maestro(client_id, data.plan_maestro_id)
    if not plan:
        raise ValidationError(
            detail="plan_maestro_id no existe para el tenant",
            internal_code="INVALID_PLAN_MAESTRO_ID",
        )
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return NecesidadBrutaRead(**row)


async def update_necesidad_bruta(client_id: UUID, necesidad_id: UUID, data: NecesidadBrutaUpdate) -> NecesidadBrutaRead:
    actual = await _get(client_id, necesidad_id)
    if not actual:
        raise NotFoundError(f"Necesidad bruta {necesidad_id} no encontrada")

    payload = data.model_dump(exclude_none=True)

    # Consistencia tenant: plan_maestro_id debe existir en el mismo cliente_id.
    plan_id = payload.get("plan_maestro_id")
    if plan_id is not None:
        plan = await _get_plan_maestro(client_id, plan_id)
        if not plan:
            raise ValidationError(
                detail="plan_maestro_id no existe para el tenant",
                internal_code="INVALID_PLAN_MAESTRO_ID",
            )

    # Validaciones puntuales en updates (porque en Update los campos son opcionales).
    if "cantidad_requerida" in payload:
        cantidad = payload.get("cantidad_requerida")
        if cantidad is not None and Decimal(str(cantidad)) <= 0:
            raise ValidationError(
                detail="cantidad_requerida debe ser mayor a 0",
                internal_code="INVALID_CANTIDAD_REQUERIDA",
            )

    if "prioridad" in payload:
        prioridad = payload.get("prioridad")
        if prioridad is not None and int(prioridad) <= 0:
            raise ValidationError(
                detail="prioridad debe ser mayor a 0",
                internal_code="INVALID_PRIORIDAD",
            )

    row = await _update(client_id, necesidad_id, payload)
    if not row:
        raise NotFoundError(f"Necesidad bruta {necesidad_id} no encontrada")
    return NecesidadBrutaRead(**row)
