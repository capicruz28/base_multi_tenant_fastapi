"""Servicio aplicacion svc_orden_servicio."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.svc import (
    list_orden_servicio as _list,
    get_orden_servicio_by_id as _get,
    create_orden_servicio as _create,
    update_orden_servicio as _update,
)
from app.modules.svc.presentation.schemas import (
    OrdenServicioCreate,
    OrdenServicioUpdate,
    OrdenServicioRead,
)
from app.core.exceptions import NotFoundError


async def list_orden_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    cliente_venta_id: Optional[UUID] = None,
    tipo_servicio: Optional[str] = None,
    buscar: Optional[str] = None,
) -> List[OrdenServicioRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        estado=estado,
        cliente_venta_id=cliente_venta_id,
        tipo_servicio=tipo_servicio,
        buscar=buscar,
    )
    return [OrdenServicioRead(**dict(r)) for r in rows]


async def get_orden_servicio_by_id(
    client_id: UUID, orden_servicio_id: UUID
) -> OrdenServicioRead:
    row = await _get(client_id, orden_servicio_id)
    if not row:
        raise NotFoundError("Orden de servicio no encontrada")
    return OrdenServicioRead(**dict(row))


async def create_orden_servicio(
    client_id: UUID, data: OrdenServicioCreate
) -> OrdenServicioRead:
    dump = data.model_dump(exclude_none=True)
    row = await _create(client_id, dump)
    return OrdenServicioRead(**dict(row))


async def update_orden_servicio(
    client_id: UUID, orden_servicio_id: UUID, data: OrdenServicioUpdate
) -> OrdenServicioRead:
    dump = data.model_dump(exclude_none=True)
    row = await _update(client_id, orden_servicio_id, dump)
    if not row:
        raise NotFoundError("Orden de servicio no encontrada")
    return OrdenServicioRead(**dict(row))
