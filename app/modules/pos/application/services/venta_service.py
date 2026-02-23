"""
Servicios de aplicación para pos_venta.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.infrastructure.database.queries.pos import (
    list_ventas as _list_ventas,
    get_venta_by_id as _get_venta_by_id,
    create_venta as _create_venta,
    update_venta as _update_venta,
)
from app.modules.pos.presentation.schemas import (
    VentaCreate,
    VentaUpdate,
    VentaRead,
)
from app.core.exceptions import NotFoundError


async def list_ventas(
    client_id: UUID,
    punto_venta_id: Optional[UUID] = None,
    turno_caja_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
) -> List[VentaRead]:
    """Lista ventas POS del tenant."""
    rows = await _list_ventas(
        client_id=client_id,
        punto_venta_id=punto_venta_id,
        turno_caja_id=turno_caja_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return [VentaRead(**row) for row in rows]


async def get_venta_by_id(client_id: UUID, venta_id: UUID) -> VentaRead:
    """Obtiene una venta POS por id."""
    row = await _get_venta_by_id(client_id, venta_id)
    if not row:
        raise NotFoundError(f"Venta {venta_id} no encontrada")
    return VentaRead(**row)


async def create_venta(client_id: UUID, data: VentaCreate) -> VentaRead:
    """Crea una venta POS."""
    row = await _create_venta(client_id, data.model_dump(exclude_none=True))
    return VentaRead(**row)


async def update_venta(
    client_id: UUID, venta_id: UUID, data: VentaUpdate
) -> VentaRead:
    """Actualiza una venta POS (ej. anulación)."""
    row = await _update_venta(
        client_id, venta_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Venta {venta_id} no encontrada")
    return VentaRead(**row)
