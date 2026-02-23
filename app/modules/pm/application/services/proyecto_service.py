"""Servicio aplicacion pm_proyecto."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.pm import (
    list_proyecto as _list,
    get_proyecto_by_id as _get,
    create_proyecto as _create,
    update_proyecto as _update,
)
from app.modules.pm.presentation.schemas import (
    ProyectoCreate,
    ProyectoUpdate,
    ProyectoRead,
)
from app.core.exceptions import NotFoundError


async def list_proyecto(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    cliente_venta_id: Optional[UUID] = None,
    buscar: Optional[str] = None,
) -> List[ProyectoRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        estado=estado,
        cliente_venta_id=cliente_venta_id,
        buscar=buscar,
    )
    return [ProyectoRead(**dict(r)) for r in rows]


async def get_proyecto_by_id(client_id: UUID, proyecto_id: UUID) -> ProyectoRead:
    row = await _get(client_id, proyecto_id)
    if not row:
        raise NotFoundError("Proyecto no encontrado")
    return ProyectoRead(**dict(row))


async def create_proyecto(client_id: UUID, data: ProyectoCreate) -> ProyectoRead:
    dump = data.model_dump(exclude_none=True)
    row = await _create(client_id, dump)
    return ProyectoRead(**dict(row))


async def update_proyecto(
    client_id: UUID, proyecto_id: UUID, data: ProyectoUpdate
) -> ProyectoRead:
    dump = data.model_dump(exclude_none=True)
    row = await _update(client_id, proyecto_id, dump)
    if not row:
        raise NotFoundError("Proyecto no encontrado")
    return ProyectoRead(**dict(row))
