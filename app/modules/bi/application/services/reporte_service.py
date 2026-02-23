# app/modules/bi/application/services/reporte_service.py
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.bi import (
    list_reporte as _list,
    get_reporte_by_id as _get,
    create_reporte as _create,
    update_reporte as _update,
)
from app.modules.bi.presentation.schemas import (
    ReporteCreate,
    ReporteUpdate,
    ReporteRead,
)
from app.core.exceptions import NotFoundError


async def list_reporte(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_reporte: Optional[str] = None,
    modulo_origen: Optional[str] = None,
    categoria: Optional[str] = None,
    es_activo: Optional[bool] = None,
    es_publico: Optional[bool] = None,
    buscar: Optional[str] = None,
) -> List[ReporteRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        tipo_reporte=tipo_reporte,
        modulo_origen=modulo_origen,
        categoria=categoria,
        es_activo=es_activo,
        es_publico=es_publico,
        buscar=buscar,
    )
    return [ReporteRead(**dict(r)) for r in rows]


async def get_reporte_by_id(client_id: UUID, reporte_id: UUID) -> ReporteRead:
    row = await _get(client_id, reporte_id)
    if not row:
        raise NotFoundError("Reporte no encontrado")
    return ReporteRead(**dict(row))


async def create_reporte(client_id: UUID, data: ReporteCreate) -> ReporteRead:
    dump = data.model_dump(exclude_none=True)
    row = await _create(client_id, dump)
    return ReporteRead(**dict(row))


async def update_reporte(
    client_id: UUID, reporte_id: UUID, data: ReporteUpdate
) -> ReporteRead:
    dump = data.model_dump(exclude_none=True)
    row = await _update(client_id, reporte_id, dump)
    if not row:
        raise NotFoundError("Reporte no encontrado")
    return ReporteRead(**dict(row))
