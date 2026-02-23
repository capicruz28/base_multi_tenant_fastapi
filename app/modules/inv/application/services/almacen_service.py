# app/modules/inv/application/services/almacen_service.py
"""
Servicio de Almacén (INV). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.inv import (
    list_almacenes,
    get_almacen_by_id,
    create_almacen,
    update_almacen,
)
from app.modules.inv.presentation.schemas import (
    AlmacenCreate,
    AlmacenUpdate,
    AlmacenRead,
)


def _row_to_read(row: dict) -> AlmacenRead:
    return AlmacenRead(**row)


async def list_almacenes_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    sucursal_id: Optional[UUID] = None,
    solo_activos: bool = True,
) -> List[AlmacenRead]:
    rows = await list_almacenes(
        client_id=client_id,
        empresa_id=empresa_id,
        sucursal_id=sucursal_id,
        solo_activos=solo_activos
    )
    return [_row_to_read(r) for r in rows]


async def get_almacen_servicio(
    client_id: UUID,
    almacen_id: UUID,
) -> AlmacenRead:
    row = await get_almacen_by_id(client_id=client_id, almacen_id=almacen_id)
    if not row:
        raise NotFoundError(detail="Almacén no encontrado")
    return _row_to_read(row)


async def create_almacen_servicio(
    client_id: UUID,
    data: AlmacenCreate,
) -> AlmacenRead:
    payload = data.model_dump()
    row = await create_almacen(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_almacen_servicio(
    client_id: UUID,
    almacen_id: UUID,
    data: AlmacenUpdate,
) -> AlmacenRead:
    row = await get_almacen_by_id(client_id=client_id, almacen_id=almacen_id)
    if not row:
        raise NotFoundError(detail="Almacén no encontrado")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_almacen(client_id=client_id, almacen_id=almacen_id, data=payload)
    return _row_to_read(updated)
