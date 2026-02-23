"""
Servicios de aplicación para pos_venta_detalle.
"""
from typing import List, Optional
from uuid import UUID

from app.infrastructure.database.queries.pos import (
    list_venta_detalles as _list_venta_detalles,
    get_venta_detalle_by_id as _get_venta_detalle_by_id,
    create_venta_detalle as _create_venta_detalle,
    update_venta_detalle as _update_venta_detalle,
)
from app.modules.pos.presentation.schemas import (
    VentaDetalleCreate,
    VentaDetalleUpdate,
    VentaDetalleRead,
)
from app.core.exceptions import NotFoundError


async def list_venta_detalles(
    client_id: UUID,
    venta_id: Optional[UUID] = None,
) -> List[VentaDetalleRead]:
    """Lista detalles de venta POS del tenant."""
    rows = await _list_venta_detalles(client_id=client_id, venta_id=venta_id)
    return [VentaDetalleRead(**row) for row in rows]


async def get_venta_detalle_by_id(
    client_id: UUID, venta_detalle_id: UUID
) -> VentaDetalleRead:
    """Obtiene un detalle de venta por id."""
    row = await _get_venta_detalle_by_id(client_id, venta_detalle_id)
    if not row:
        raise NotFoundError(f"Detalle de venta {venta_detalle_id} no encontrado")
    return VentaDetalleRead(**row)


async def create_venta_detalle(
    client_id: UUID, data: VentaDetalleCreate
) -> VentaDetalleRead:
    """Crea un detalle de venta."""
    row = await _create_venta_detalle(client_id, data.model_dump(exclude_none=True))
    return VentaDetalleRead(**row)


async def update_venta_detalle(
    client_id: UUID, venta_detalle_id: UUID, data: VentaDetalleUpdate
) -> VentaDetalleRead:
    """Actualiza un detalle de venta."""
    row = await _update_venta_detalle(
        client_id, venta_detalle_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Detalle de venta {venta_detalle_id} no encontrado")
    return VentaDetalleRead(**row)
