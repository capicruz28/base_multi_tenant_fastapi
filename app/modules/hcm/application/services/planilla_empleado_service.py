"""Servicios de aplicación para hcm_planilla_empleado."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.hcm import (
    list_planilla_empleados as _list,
    get_planilla_empleado_by_id as _get,
    create_planilla_empleado as _create,
    update_planilla_empleado as _update,
)
from app.modules.hcm.presentation.schemas import PlanillaEmpleadoCreate, PlanillaEmpleadoUpdate, PlanillaEmpleadoRead
from app.core.exceptions import NotFoundError


async def list_planilla_empleados(
    client_id: UUID,
    planilla_id: Optional[UUID] = None,
    empleado_id: Optional[UUID] = None,
) -> List[PlanillaEmpleadoRead]:
    rows = await _list(
        client_id=client_id,
        planilla_id=planilla_id,
        empleado_id=empleado_id,
    )
    return [PlanillaEmpleadoRead(**r) for r in rows]


async def get_planilla_empleado_by_id(
    client_id: UUID, planilla_empleado_id: UUID
) -> PlanillaEmpleadoRead:
    row = await _get(client_id, planilla_empleado_id)
    if not row:
        raise NotFoundError(f"Planilla empleado {planilla_empleado_id} no encontrado")
    return PlanillaEmpleadoRead(**row)


async def create_planilla_empleado(
    client_id: UUID, data: PlanillaEmpleadoCreate
) -> PlanillaEmpleadoRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return PlanillaEmpleadoRead(**row)


async def update_planilla_empleado(
    client_id: UUID, planilla_empleado_id: UUID, data: PlanillaEmpleadoUpdate
) -> PlanillaEmpleadoRead:
    row = await _update(client_id, planilla_empleado_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Planilla empleado {planilla_empleado_id} no encontrado")
    return PlanillaEmpleadoRead(**row)
