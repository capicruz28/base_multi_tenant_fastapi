"""Servicio aplicación mps_plan_produccion."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.mps import (
    list_plan_produccion as _list,
    get_plan_produccion_by_id as _get,
    create_plan_produccion as _create,
    update_plan_produccion as _update,
)
from app.modules.mps.presentation.schemas import PlanProduccionCreate, PlanProduccionUpdate, PlanProduccionRead
from app.core.exceptions import NotFoundError


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
    row = await _update(client_id, plan_produccion_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Plan de producción {plan_produccion_id} no encontrado")
    return PlanProduccionRead(**row)
