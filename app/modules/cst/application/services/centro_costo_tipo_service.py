"""Servicio aplicacion cst_centro_costo_tipo."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.cst import (
    list_centro_costo_tipo as _list,
    get_centro_costo_tipo_by_id as _get,
    create_centro_costo_tipo as _create,
    update_centro_costo_tipo as _update,
)
from app.modules.cst.presentation.schemas import CentroCostoTipoCreate, CentroCostoTipoUpdate, CentroCostoTipoRead
from app.core.exceptions import NotFoundError


async def list_centro_costo_tipo(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_clasificacion: Optional[str] = None,
    es_activo: Optional[bool] = None,
    buscar: Optional[str] = None,
) -> List[CentroCostoTipoRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        tipo_clasificacion=tipo_clasificacion,
        es_activo=es_activo,
        buscar=buscar,
    )
    return [CentroCostoTipoRead(**dict(r)) for r in rows]


async def get_centro_costo_tipo_by_id(client_id: UUID, cc_tipo_id: UUID) -> CentroCostoTipoRead:
    row = await _get(client_id, cc_tipo_id)
    if not row:
        raise NotFoundError("Tipo de centro de costo no encontrado")
    return CentroCostoTipoRead(**dict(row))


async def create_centro_costo_tipo(client_id: UUID, data: CentroCostoTipoCreate) -> CentroCostoTipoRead:
    dump = data.model_dump(exclude_none=True)
    row = await _create(client_id, dump)
    return CentroCostoTipoRead(**dict(row))


async def update_centro_costo_tipo(
    client_id: UUID, cc_tipo_id: UUID, data: CentroCostoTipoUpdate
) -> CentroCostoTipoRead:
    dump = data.model_dump(exclude_none=True)
    row = await _update(client_id, cc_tipo_id, dump)
    if not row:
        raise NotFoundError("Tipo de centro de costo no encontrado")
    return CentroCostoTipoRead(**dict(row))
