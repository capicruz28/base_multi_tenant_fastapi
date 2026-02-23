# app/modules/inv/application/services/unidad_medida_service.py
"""
Servicio de Unidad de Medida (INV). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.inv import (
    list_unidades_medida,
    get_unidad_medida_by_id,
    create_unidad_medida,
    update_unidad_medida,
)
from app.modules.inv.presentation.schemas import (
    UnidadMedidaCreate,
    UnidadMedidaUpdate,
    UnidadMedidaRead,
)


def _row_to_read(row: dict) -> UnidadMedidaRead:
    return UnidadMedidaRead(**row)


async def list_unidades_medida_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    solo_activos: bool = True,
) -> List[UnidadMedidaRead]:
    rows = await list_unidades_medida(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos
    )
    return [_row_to_read(r) for r in rows]


async def get_unidad_medida_servicio(
    client_id: UUID,
    unidad_medida_id: UUID,
) -> UnidadMedidaRead:
    row = await get_unidad_medida_by_id(client_id=client_id, unidad_medida_id=unidad_medida_id)
    if not row:
        raise NotFoundError(detail="Unidad de medida no encontrada")
    return _row_to_read(row)


async def create_unidad_medida_servicio(
    client_id: UUID,
    data: UnidadMedidaCreate,
) -> UnidadMedidaRead:
    payload = data.model_dump()
    row = await create_unidad_medida(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_unidad_medida_servicio(
    client_id: UUID,
    unidad_medida_id: UUID,
    data: UnidadMedidaUpdate,
) -> UnidadMedidaRead:
    row = await get_unidad_medida_by_id(client_id=client_id, unidad_medida_id=unidad_medida_id)
    if not row:
        raise NotFoundError(detail="Unidad de medida no encontrada")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_unidad_medida(client_id=client_id, unidad_medida_id=unidad_medida_id, data=payload)
    return _row_to_read(updated)
