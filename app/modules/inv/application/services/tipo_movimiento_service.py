# app/modules/inv/application/services/tipo_movimiento_service.py
"""
Servicio de Tipo de Movimiento (INV). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.inv import (
    list_tipos_movimiento,
    get_tipo_movimiento_by_id,
    create_tipo_movimiento,
    update_tipo_movimiento,
)
from app.modules.inv.presentation.schemas import (
    TipoMovimientoCreate,
    TipoMovimientoUpdate,
    TipoMovimientoRead,
)


def _row_to_read(row: dict) -> TipoMovimientoRead:
    return TipoMovimientoRead(**row)


async def list_tipos_movimiento_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    solo_activos: bool = True,
) -> List[TipoMovimientoRead]:
    rows = await list_tipos_movimiento(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos
    )
    return [_row_to_read(r) for r in rows]


async def get_tipo_movimiento_servicio(
    client_id: UUID,
    tipo_movimiento_id: UUID,
) -> TipoMovimientoRead:
    row = await get_tipo_movimiento_by_id(client_id=client_id, tipo_movimiento_id=tipo_movimiento_id)
    if not row:
        raise NotFoundError(detail="Tipo de movimiento no encontrado")
    return _row_to_read(row)


async def create_tipo_movimiento_servicio(
    client_id: UUID,
    data: TipoMovimientoCreate,
) -> TipoMovimientoRead:
    payload = data.model_dump()
    row = await create_tipo_movimiento(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_tipo_movimiento_servicio(
    client_id: UUID,
    tipo_movimiento_id: UUID,
    data: TipoMovimientoUpdate,
) -> TipoMovimientoRead:
    row = await get_tipo_movimiento_by_id(client_id=client_id, tipo_movimiento_id=tipo_movimiento_id)
    if not row:
        raise NotFoundError(detail="Tipo de movimiento no encontrado")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_tipo_movimiento(client_id=client_id, tipo_movimiento_id=tipo_movimiento_id, data=payload)
    return _row_to_read(updated)
