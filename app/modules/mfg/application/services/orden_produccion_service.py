"""Servicio aplicación mfg_orden_produccion."""
from typing import List, Optional
from uuid import UUID
from datetime import date
from app.infrastructure.database.queries.mfg import (
    list_ordenes_produccion as _list,
    get_orden_produccion_by_id as _get,
    create_orden_produccion as _create,
    update_orden_produccion as _update,
)
from app.modules.mfg.presentation.schemas import OrdenProduccionCreate, OrdenProduccionUpdate, OrdenProduccionRead
from app.core.exceptions import NotFoundError

async def list_ordenes_produccion(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> List[OrdenProduccionRead]:
    rows = await _list(client_id=client_id, empresa_id=empresa_id, producto_id=producto_id, estado=estado, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
    return [OrdenProduccionRead(**r) for r in rows]

async def get_orden_produccion_by_id(client_id: UUID, orden_produccion_id: UUID) -> OrdenProduccionRead:
    row = await _get(client_id, orden_produccion_id)
    if not row:
        raise NotFoundError(f"Orden de producción {orden_produccion_id} no encontrada")
    return OrdenProduccionRead(**row)

async def create_orden_produccion(client_id: UUID, data: OrdenProduccionCreate) -> OrdenProduccionRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return OrdenProduccionRead(**row)

async def update_orden_produccion(client_id: UUID, orden_produccion_id: UUID, data: OrdenProduccionUpdate) -> OrdenProduccionRead:
    row = await _update(client_id, orden_produccion_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Orden de producción {orden_produccion_id} no encontrada")
    return OrdenProduccionRead(**row)
