"""
Servicio de Inventario Físico Detalle (INV). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.inv import (
    list_inventarios_fisicos_detalle,
    get_inventario_fisico_detalle_by_id,
    create_inventario_fisico_detalle,
    update_inventario_fisico_detalle,
)
from app.modules.inv.presentation.schemas import (
    InventarioFisicoDetalleCreate,
    InventarioFisicoDetalleUpdate,
    InventarioFisicoDetalleRead,
)


def _row_to_read(row: dict) -> InventarioFisicoDetalleRead:
    return InventarioFisicoDetalleRead(**row)


async def list_inventarios_fisicos_detalle_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    inventario_fisico_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
) -> List[InventarioFisicoDetalleRead]:
    rows = await list_inventarios_fisicos_detalle(
        client_id=client_id,
        empresa_id=empresa_id,
        inventario_fisico_id=inventario_fisico_id,
        producto_id=producto_id,
    )
    return [_row_to_read(r) for r in rows]


async def get_inventario_fisico_detalle_servicio(
    client_id: UUID,
    inventario_fisico_detalle_id: UUID,
) -> InventarioFisicoDetalleRead:
    row = await get_inventario_fisico_detalle_by_id(
        client_id=client_id, inventario_fisico_detalle_id=inventario_fisico_detalle_id
    )
    if not row:
        raise NotFoundError(detail="Detalle de inventario físico no encontrado")
    return _row_to_read(row)


async def create_inventario_fisico_detalle_servicio(
    client_id: UUID,
    data: InventarioFisicoDetalleCreate,
) -> InventarioFisicoDetalleRead:
    payload = data.model_dump()
    row = await create_inventario_fisico_detalle(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_inventario_fisico_detalle_servicio(
    client_id: UUID,
    inventario_fisico_detalle_id: UUID,
    data: InventarioFisicoDetalleUpdate,
) -> InventarioFisicoDetalleRead:
    row = await get_inventario_fisico_detalle_by_id(
        client_id=client_id, inventario_fisico_detalle_id=inventario_fisico_detalle_id
    )
    if not row:
        raise NotFoundError(detail="Detalle de inventario físico no encontrado")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_inventario_fisico_detalle(
        client_id=client_id,
        inventario_fisico_detalle_id=inventario_fisico_detalle_id,
        data=payload,
    )
    return _row_to_read(updated)

