# app/modules/org/application/services/centro_costo_service.py
"""Servicio de Centro de Costo (ORG). client_id desde contexto."""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.org import (
    list_centros_costo,
    get_centro_costo_by_id,
    create_centro_costo,
    update_centro_costo,
)
from app.modules.org.presentation.schemas import (
    CentroCostoCreate,
    CentroCostoUpdate,
    CentroCostoRead,
)


def _row_to_read(row: dict) -> CentroCostoRead:
    return CentroCostoRead(**row)


async def list_centros_costo_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    solo_activos: bool = True,
) -> List[CentroCostoRead]:
    rows = await list_centros_costo(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
    )
    return [_row_to_read(r) for r in rows]


async def get_centro_costo_servicio(
    client_id: UUID,
    centro_costo_id: UUID,
) -> CentroCostoRead:
    row = await get_centro_costo_by_id(
        client_id=client_id,
        centro_costo_id=centro_costo_id,
    )
    if not row:
        raise NotFoundError(detail="Centro de costo no encontrado")
    return _row_to_read(row)


async def create_centro_costo_servicio(
    client_id: UUID,
    data: CentroCostoCreate,
) -> CentroCostoRead:
    payload = data.model_dump()
    row = await create_centro_costo(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_centro_costo_servicio(
    client_id: UUID,
    centro_costo_id: UUID,
    data: CentroCostoUpdate,
) -> CentroCostoRead:
    row = await get_centro_costo_by_id(
        client_id=client_id,
        centro_costo_id=centro_costo_id,
    )
    if not row:
        raise NotFoundError(detail="Centro de costo no encontrado")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_centro_costo(
        client_id=client_id,
        centro_costo_id=centro_costo_id,
        data=payload,
    )
    return _row_to_read(updated)
