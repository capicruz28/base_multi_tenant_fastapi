"""Servicio aplicación mrp_plan_maestro."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.mrp import (
    list_plan_maestro as _list,
    get_plan_maestro_by_id as _get,
    create_plan_maestro as _create,
    update_plan_maestro as _update,
)
from app.modules.mrp.presentation.schemas import PlanMaestroCreate, PlanMaestroUpdate, PlanMaestroRead
from app.core.exceptions import NotFoundError


async def list_plan_maestro(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    buscar: Optional[str] = None,
) -> List[PlanMaestroRead]:
    rows = await _list(client_id=client_id, empresa_id=empresa_id, estado=estado, buscar=buscar)
    return [PlanMaestroRead(**r) for r in rows]


async def get_plan_maestro_by_id(client_id: UUID, plan_maestro_id: UUID) -> PlanMaestroRead:
    row = await _get(client_id, plan_maestro_id)
    if not row:
        raise NotFoundError(f"Plan maestro {plan_maestro_id} no encontrado")
    return PlanMaestroRead(**row)


async def create_plan_maestro(client_id: UUID, data: PlanMaestroCreate) -> PlanMaestroRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return PlanMaestroRead(**row)


async def update_plan_maestro(client_id: UUID, plan_maestro_id: UUID, data: PlanMaestroUpdate) -> PlanMaestroRead:
    row = await _update(client_id, plan_maestro_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Plan maestro {plan_maestro_id} no encontrado")
    return PlanMaestroRead(**row)
