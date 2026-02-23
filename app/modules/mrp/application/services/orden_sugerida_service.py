"""Servicio aplicación mrp_orden_sugerida."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.mrp import (
    list_orden_sugerida as _list,
    get_orden_sugerida_by_id as _get,
    create_orden_sugerida as _create,
    update_orden_sugerida as _update,
)
from app.modules.mrp.presentation.schemas import OrdenSugeridaCreate, OrdenSugeridaUpdate, OrdenSugeridaRead
from app.core.exceptions import NotFoundError


async def list_orden_sugerida(
    client_id: UUID,
    plan_maestro_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    tipo_orden: Optional[str] = None,
) -> List[OrdenSugeridaRead]:
    rows = await _list(
        client_id=client_id,
        plan_maestro_id=plan_maestro_id,
        producto_id=producto_id,
        estado=estado,
        tipo_orden=tipo_orden,
    )
    return [OrdenSugeridaRead(**r) for r in rows]


async def get_orden_sugerida_by_id(client_id: UUID, orden_sugerida_id: UUID) -> OrdenSugeridaRead:
    row = await _get(client_id, orden_sugerida_id)
    if not row:
        raise NotFoundError(f"Orden sugerida {orden_sugerida_id} no encontrada")
    return OrdenSugeridaRead(**row)


async def create_orden_sugerida(client_id: UUID, data: OrdenSugeridaCreate) -> OrdenSugeridaRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return OrdenSugeridaRead(**row)


async def update_orden_sugerida(
    client_id: UUID, orden_sugerida_id: UUID, data: OrdenSugeridaUpdate
) -> OrdenSugeridaRead:
    row = await _update(client_id, orden_sugerida_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Orden sugerida {orden_sugerida_id} no encontrada")
    return OrdenSugeridaRead(**row)
