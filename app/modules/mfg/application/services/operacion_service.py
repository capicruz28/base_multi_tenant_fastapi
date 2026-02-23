"""Servicio aplicación mfg_operacion."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.mfg import (
    list_operaciones as _list,
    get_operacion_by_id as _get,
    create_operacion as _create,
    update_operacion as _update,
)
from app.modules.mfg.presentation.schemas import OperacionCreate, OperacionUpdate, OperacionRead
from app.core.exceptions import NotFoundError

async def list_operaciones(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    centro_trabajo_id: Optional[UUID] = None,
    es_activo: Optional[bool] = None,
    buscar: Optional[str] = None,
) -> List[OperacionRead]:
    rows = await _list(client_id=client_id, empresa_id=empresa_id, centro_trabajo_id=centro_trabajo_id, es_activo=es_activo, buscar=buscar)
    return [OperacionRead(**r) for r in rows]

async def get_operacion_by_id(client_id: UUID, operacion_id: UUID) -> OperacionRead:
    row = await _get(client_id, operacion_id)
    if not row:
        raise NotFoundError(f"Operación {operacion_id} no encontrada")
    return OperacionRead(**row)

async def create_operacion(client_id: UUID, data: OperacionCreate) -> OperacionRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return OperacionRead(**row)

async def update_operacion(client_id: UUID, operacion_id: UUID, data: OperacionUpdate) -> OperacionRead:
    row = await _update(client_id, operacion_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Operación {operacion_id} no encontrada")
    return OperacionRead(**row)
