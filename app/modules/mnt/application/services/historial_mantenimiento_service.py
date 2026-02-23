"""Servicio aplicación mnt_historial_mantenimiento."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.mnt import (
    list_historial_mantenimiento as _list,
    get_historial_mantenimiento_by_id as _get,
    create_historial_mantenimiento as _create,
    update_historial_mantenimiento as _update,
)
from app.modules.mnt.presentation.schemas import (
    HistorialMantenimientoCreate,
    HistorialMantenimientoUpdate,
    HistorialMantenimientoRead,
)
from app.core.exceptions import NotFoundError


async def list_historial_mantenimiento(
    client_id: UUID,
    activo_id: Optional[UUID] = None,
    orden_trabajo_id: Optional[UUID] = None,
    tipo_mantenimiento: Optional[str] = None,
) -> List[HistorialMantenimientoRead]:
    rows = await _list(
        client_id=client_id,
        activo_id=activo_id,
        orden_trabajo_id=orden_trabajo_id,
        tipo_mantenimiento=tipo_mantenimiento,
    )
    return [HistorialMantenimientoRead(**r) for r in rows]


async def get_historial_mantenimiento_by_id(
    client_id: UUID, historial_id: UUID
) -> HistorialMantenimientoRead:
    row = await _get(client_id, historial_id)
    if not row:
        raise NotFoundError(f"Historial mantenimiento {historial_id} no encontrado")
    return HistorialMantenimientoRead(**row)


async def create_historial_mantenimiento(
    client_id: UUID, data: HistorialMantenimientoCreate
) -> HistorialMantenimientoRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return HistorialMantenimientoRead(**row)


async def update_historial_mantenimiento(
    client_id: UUID, historial_id: UUID, data: HistorialMantenimientoUpdate
) -> HistorialMantenimientoRead:
    row = await _update(client_id, historial_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Historial mantenimiento {historial_id} no encontrado")
    return HistorialMantenimientoRead(**row)
