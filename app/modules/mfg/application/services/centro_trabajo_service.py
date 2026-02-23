"""Servicio aplicación mfg_centro_trabajo."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.mfg import (
    list_centros_trabajo as _list,
    get_centro_trabajo_by_id as _get,
    create_centro_trabajo as _create,
    update_centro_trabajo as _update,
)
from app.modules.mfg.presentation.schemas import CentroTrabajoCreate, CentroTrabajoUpdate, CentroTrabajoRead
from app.core.exceptions import NotFoundError

async def list_centros_trabajo(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    estado_centro: Optional[str] = None,
    es_activo: Optional[bool] = None,
    buscar: Optional[str] = None,
) -> List[CentroTrabajoRead]:
    rows = await _list(client_id=client_id, empresa_id=empresa_id, estado_centro=estado_centro, es_activo=es_activo, buscar=buscar)
    return [CentroTrabajoRead(**r) for r in rows]

async def get_centro_trabajo_by_id(client_id: UUID, centro_trabajo_id: UUID) -> CentroTrabajoRead:
    row = await _get(client_id, centro_trabajo_id)
    if not row:
        raise NotFoundError(f"Centro de trabajo {centro_trabajo_id} no encontrado")
    return CentroTrabajoRead(**row)

async def create_centro_trabajo(client_id: UUID, data: CentroTrabajoCreate) -> CentroTrabajoRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return CentroTrabajoRead(**row)

async def update_centro_trabajo(client_id: UUID, centro_trabajo_id: UUID, data: CentroTrabajoUpdate) -> CentroTrabajoRead:
    row = await _update(client_id, centro_trabajo_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Centro de trabajo {centro_trabajo_id} no encontrado")
    return CentroTrabajoRead(**row)
