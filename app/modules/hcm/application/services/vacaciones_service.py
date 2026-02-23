"""Servicios de aplicación para hcm_vacaciones."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.hcm import (
    list_vacaciones as _list,
    get_vacaciones_by_id as _get,
    create_vacaciones as _create,
    update_vacaciones as _update,
)
from app.modules.hcm.presentation.schemas import VacacionesCreate, VacacionesUpdate, VacacionesRead
from app.core.exceptions import NotFoundError


async def list_vacaciones(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    empleado_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    año_periodo: Optional[int] = None,
) -> List[VacacionesRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        empleado_id=empleado_id,
        estado=estado,
        año_periodo=año_periodo,
    )
    return [VacacionesRead(**r) for r in rows]


async def get_vacaciones_by_id(client_id: UUID, vacaciones_id: UUID) -> VacacionesRead:
    row = await _get(client_id, vacaciones_id)
    if not row:
        raise NotFoundError(f"Vacaciones {vacaciones_id} no encontradas")
    return VacacionesRead(**row)


async def create_vacaciones(client_id: UUID, data: VacacionesCreate) -> VacacionesRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return VacacionesRead(**row)


async def update_vacaciones(
    client_id: UUID, vacaciones_id: UUID, data: VacacionesUpdate
) -> VacacionesRead:
    row = await _update(client_id, vacaciones_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Vacaciones {vacaciones_id} no encontradas")
    return VacacionesRead(**row)
