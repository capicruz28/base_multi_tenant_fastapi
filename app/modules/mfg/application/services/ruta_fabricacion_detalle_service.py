"""Servicio aplicación mfg_ruta_fabricacion_detalle."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.mfg import (
    list_ruta_fabricacion_detalles as _list,
    get_ruta_fabricacion_detalle_by_id as _get,
    create_ruta_fabricacion_detalle as _create,
    update_ruta_fabricacion_detalle as _update,
)
from app.modules.mfg.presentation.schemas import RutaFabricacionDetalleCreate, RutaFabricacionDetalleUpdate, RutaFabricacionDetalleRead
from app.core.exceptions import NotFoundError

async def list_ruta_fabricacion_detalles(client_id: UUID, ruta_id: Optional[UUID] = None) -> List[RutaFabricacionDetalleRead]:
    rows = await _list(client_id=client_id, ruta_id=ruta_id)
    return [RutaFabricacionDetalleRead(**r) for r in rows]

async def get_ruta_fabricacion_detalle_by_id(client_id: UUID, ruta_detalle_id: UUID) -> RutaFabricacionDetalleRead:
    row = await _get(client_id, ruta_detalle_id)
    if not row:
        raise NotFoundError(f"Detalle ruta {ruta_detalle_id} no encontrado")
    return RutaFabricacionDetalleRead(**row)

async def create_ruta_fabricacion_detalle(client_id: UUID, data: RutaFabricacionDetalleCreate) -> RutaFabricacionDetalleRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return RutaFabricacionDetalleRead(**row)

async def update_ruta_fabricacion_detalle(client_id: UUID, ruta_detalle_id: UUID, data: RutaFabricacionDetalleUpdate) -> RutaFabricacionDetalleRead:
    row = await _update(client_id, ruta_detalle_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Detalle ruta {ruta_detalle_id} no encontrado")
    return RutaFabricacionDetalleRead(**row)
