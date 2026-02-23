# app/modules/wfl/application/services/flujo_trabajo_service.py
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.wfl import (
    list_flujo_trabajo as _list,
    get_flujo_trabajo_by_id as _get,
    create_flujo_trabajo as _create,
    update_flujo_trabajo as _update,
)
from app.modules.wfl.presentation.schemas import (
    FlujoTrabajoCreate,
    FlujoTrabajoUpdate,
    FlujoTrabajoRead,
)
from app.core.exceptions import NotFoundError


async def list_flujo_trabajo(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_flujo: Optional[str] = None,
    modulo_aplicable: Optional[str] = None,
    es_activo: Optional[bool] = None,
    buscar: Optional[str] = None,
) -> List[FlujoTrabajoRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        tipo_flujo=tipo_flujo,
        modulo_aplicable=modulo_aplicable,
        es_activo=es_activo,
        buscar=buscar,
    )
    return [FlujoTrabajoRead(**dict(r)) for r in rows]


async def get_flujo_trabajo_by_id(client_id: UUID, flujo_id: UUID) -> FlujoTrabajoRead:
    row = await _get(client_id, flujo_id)
    if not row:
        raise NotFoundError("Flujo de trabajo no encontrado")
    return FlujoTrabajoRead(**dict(row))


async def create_flujo_trabajo(client_id: UUID, data: FlujoTrabajoCreate) -> FlujoTrabajoRead:
    dump = data.model_dump(exclude_none=True)
    row = await _create(client_id, dump)
    return FlujoTrabajoRead(**dict(row))


async def update_flujo_trabajo(
    client_id: UUID, flujo_id: UUID, data: FlujoTrabajoUpdate
) -> FlujoTrabajoRead:
    dump = data.model_dump(exclude_none=True)
    row = await _update(client_id, flujo_id, dump)
    if not row:
        raise NotFoundError("Flujo de trabajo no encontrado")
    return FlujoTrabajoRead(**dict(row))
