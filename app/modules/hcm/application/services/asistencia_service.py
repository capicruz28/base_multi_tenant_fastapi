"""Servicios de aplicación para hcm_asistencia."""
from typing import List, Optional
from uuid import UUID
from datetime import date
from app.infrastructure.database.queries.hcm import (
    list_asistencias as _list,
    get_asistencia_by_id as _get,
    create_asistencia as _create,
    update_asistencia as _update,
)
from app.modules.hcm.presentation.schemas import AsistenciaCreate, AsistenciaUpdate, AsistenciaRead
from app.core.exceptions import NotFoundError


async def list_asistencias(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    empleado_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    tipo_asistencia: Optional[str] = None,
) -> List[AsistenciaRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        empleado_id=empleado_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        tipo_asistencia=tipo_asistencia,
    )
    return [AsistenciaRead(**r) for r in rows]


async def get_asistencia_by_id(client_id: UUID, asistencia_id: UUID) -> AsistenciaRead:
    row = await _get(client_id, asistencia_id)
    if not row:
        raise NotFoundError(f"Asistencia {asistencia_id} no encontrada")
    return AsistenciaRead(**row)


async def create_asistencia(client_id: UUID, data: AsistenciaCreate) -> AsistenciaRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return AsistenciaRead(**row)


async def update_asistencia(
    client_id: UUID, asistencia_id: UUID, data: AsistenciaUpdate
) -> AsistenciaRead:
    row = await _update(client_id, asistencia_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Asistencia {asistencia_id} no encontrada")
    return AsistenciaRead(**row)
