"""Servicio aplicación mfg_ruta_fabricacion."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.mfg import (
    list_rutas_fabricacion as _list,
    get_ruta_fabricacion_by_id as _get,
    create_ruta_fabricacion as _create,
    update_ruta_fabricacion as _update,
)
from app.modules.mfg.presentation.schemas import RutaFabricacionCreate, RutaFabricacionUpdate, RutaFabricacionRead
from app.core.exceptions import NotFoundError

async def list_rutas_fabricacion(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    es_ruta_activa: Optional[bool] = None,
    estado: Optional[str] = None,
    buscar: Optional[str] = None,
) -> List[RutaFabricacionRead]:
    rows = await _list(client_id=client_id, empresa_id=empresa_id, producto_id=producto_id, es_ruta_activa=es_ruta_activa, estado=estado, buscar=buscar)
    return [RutaFabricacionRead(**r) for r in rows]

async def get_ruta_fabricacion_by_id(client_id: UUID, ruta_id: UUID) -> RutaFabricacionRead:
    row = await _get(client_id, ruta_id)
    if not row:
        raise NotFoundError(f"Ruta de fabricación {ruta_id} no encontrada")
    return RutaFabricacionRead(**row)

async def create_ruta_fabricacion(client_id: UUID, data: RutaFabricacionCreate) -> RutaFabricacionRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return RutaFabricacionRead(**row)

async def update_ruta_fabricacion(client_id: UUID, ruta_id: UUID, data: RutaFabricacionUpdate) -> RutaFabricacionRead:
    row = await _update(client_id, ruta_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Ruta de fabricación {ruta_id} no encontrada")
    return RutaFabricacionRead(**row)
