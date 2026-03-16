"""
Servicio de Movimiento Detalle (INV). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.inv import (
    list_movimientos_detalle,
    get_movimiento_detalle_by_id,
    create_movimiento_detalle,
    update_movimiento_detalle,
)
from app.modules.inv.presentation.schemas import (
    MovimientoDetalleCreate,
    MovimientoDetalleUpdate,
    MovimientoDetalleRead,
)


def _row_to_read(row: dict) -> MovimientoDetalleRead:
    return MovimientoDetalleRead(**row)


async def list_movimientos_detalle_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    movimiento_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
) -> List[MovimientoDetalleRead]:
    rows = await list_movimientos_detalle(
        client_id=client_id,
        empresa_id=empresa_id,
        movimiento_id=movimiento_id,
        producto_id=producto_id,
    )
    return [_row_to_read(r) for r in rows]


async def get_movimiento_detalle_servicio(
    client_id: UUID,
    movimiento_detalle_id: UUID,
) -> MovimientoDetalleRead:
    row = await get_movimiento_detalle_by_id(
        client_id=client_id, movimiento_detalle_id=movimiento_detalle_id
    )
    if not row:
        raise NotFoundError(detail="Detalle de movimiento no encontrado")
    return _row_to_read(row)


async def create_movimiento_detalle_servicio(
    client_id: UUID,
    data: MovimientoDetalleCreate,
) -> MovimientoDetalleRead:
    payload = data.model_dump()
    row = await create_movimiento_detalle(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_movimiento_detalle_servicio(
    client_id: UUID,
    movimiento_detalle_id: UUID,
    data: MovimientoDetalleUpdate,
) -> MovimientoDetalleRead:
    row = await get_movimiento_detalle_by_id(
        client_id=client_id, movimiento_detalle_id=movimiento_detalle_id
    )
    if not row:
        raise NotFoundError(detail="Detalle de movimiento no encontrado")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_movimiento_detalle(
        client_id=client_id, movimiento_detalle_id=movimiento_detalle_id, data=payload
    )
    return _row_to_read(updated)

