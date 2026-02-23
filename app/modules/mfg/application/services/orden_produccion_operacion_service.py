"""Servicio aplicación mfg_orden_produccion_operacion."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.mfg import (
    list_orden_produccion_operaciones as _list,
    get_orden_produccion_operacion_by_id as _get,
    create_orden_produccion_operacion as _create,
    update_orden_produccion_operacion as _update,
)
from app.modules.mfg.presentation.schemas import OrdenProduccionOperacionCreate, OrdenProduccionOperacionUpdate, OrdenProduccionOperacionRead
from app.core.exceptions import NotFoundError

async def list_orden_produccion_operaciones(
    client_id: UUID,
    orden_produccion_id: Optional[UUID] = None,
    centro_trabajo_id: Optional[UUID] = None,
    estado: Optional[str] = None,
) -> List[OrdenProduccionOperacionRead]:
    rows = await _list(client_id=client_id, orden_produccion_id=orden_produccion_id, centro_trabajo_id=centro_trabajo_id, estado=estado)
    return [OrdenProduccionOperacionRead(**r) for r in rows]

async def get_orden_produccion_operacion_by_id(client_id: UUID, op_operacion_id: UUID) -> OrdenProduccionOperacionRead:
    row = await _get(client_id, op_operacion_id)
    if not row:
        raise NotFoundError(f"Operación de OP {op_operacion_id} no encontrada")
    return OrdenProduccionOperacionRead(**row)

async def create_orden_produccion_operacion(client_id: UUID, data: OrdenProduccionOperacionCreate) -> OrdenProduccionOperacionRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return OrdenProduccionOperacionRead(**row)

async def update_orden_produccion_operacion(client_id: UUID, op_operacion_id: UUID, data: OrdenProduccionOperacionUpdate) -> OrdenProduccionOperacionRead:
    row = await _update(client_id, op_operacion_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Operación de OP {op_operacion_id} no encontrada")
    return OrdenProduccionOperacionRead(**row)
