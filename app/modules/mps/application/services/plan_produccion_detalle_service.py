"""Servicio aplicación mps_plan_produccion_detalle. Calcula porcentaje_uso_capacidad si aplica."""
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from app.infrastructure.database.queries.mps import (
    list_plan_produccion_detalle as _list,
    get_plan_produccion_detalle_by_id as _get,
    create_plan_produccion_detalle as _create,
    update_plan_produccion_detalle as _update,
)
from app.modules.mps.presentation.schemas import (
    PlanProduccionDetalleCreate,
    PlanProduccionDetalleUpdate,
    PlanProduccionDetalleRead,
)
from app.core.exceptions import NotFoundError


def _enrich_detalle(row: dict) -> dict:
    r = dict(row)
    cap = r.get("capacidad_disponible") or Decimal("0")
    qty = r.get("cantidad_planificada") or Decimal("0")
    if cap and cap > 0:
        r["porcentaje_uso_capacidad"] = (qty / cap) * 100
    else:
        r["porcentaje_uso_capacidad"] = None
    return r


async def list_plan_produccion_detalle(
    client_id: UUID,
    plan_produccion_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
) -> List[PlanProduccionDetalleRead]:
    rows = await _list(
        client_id=client_id,
        plan_produccion_id=plan_produccion_id,
        producto_id=producto_id,
    )
    return [PlanProduccionDetalleRead(**_enrich_detalle(r)) for r in rows]


async def get_plan_produccion_detalle_by_id(
    client_id: UUID, plan_detalle_id: UUID
) -> PlanProduccionDetalleRead:
    row = await _get(client_id, plan_detalle_id)
    if not row:
        raise NotFoundError(f"Detalle plan producción {plan_detalle_id} no encontrado")
    return PlanProduccionDetalleRead(**_enrich_detalle(row))


async def create_plan_produccion_detalle(
    client_id: UUID, data: PlanProduccionDetalleCreate
) -> PlanProduccionDetalleRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return PlanProduccionDetalleRead(**_enrich_detalle(row))


async def update_plan_produccion_detalle(
    client_id: UUID, plan_detalle_id: UUID, data: PlanProduccionDetalleUpdate
) -> PlanProduccionDetalleRead:
    row = await _update(client_id, plan_detalle_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Detalle plan producción {plan_detalle_id} no encontrado")
    return PlanProduccionDetalleRead(**_enrich_detalle(row))
