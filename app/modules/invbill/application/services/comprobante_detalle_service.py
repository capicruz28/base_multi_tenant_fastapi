"""
Servicios de aplicación para invbill_comprobante_detalle.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID

from app.infrastructure.database.queries.invbill import (
    list_comprobante_detalles as _list_comprobante_detalles,
    get_comprobante_detalle_by_id as _get_comprobante_detalle_by_id,
    create_comprobante_detalle as _create_comprobante_detalle,
    update_comprobante_detalle as _update_comprobante_detalle,
)
from app.modules.invbill.presentation.schemas import ComprobanteDetalleCreate, ComprobanteDetalleUpdate, ComprobanteDetalleRead
from app.core.exceptions import NotFoundError


async def list_comprobante_detalles(
    client_id: UUID,
    comprobante_id: Optional[UUID] = None
) -> List[ComprobanteDetalleRead]:
    """Lista detalles de comprobantes del tenant."""
    rows = await _list_comprobante_detalles(
        client_id=client_id,
        comprobante_id=comprobante_id
    )
    return [ComprobanteDetalleRead(**row) for row in rows]


async def get_comprobante_detalle_by_id(client_id: UUID, comprobante_detalle_id: UUID) -> ComprobanteDetalleRead:
    """Obtiene un detalle por id. Lanza NotFoundError si no existe."""
    row = await _get_comprobante_detalle_by_id(client_id, comprobante_detalle_id)
    if not row:
        raise NotFoundError(f"Detalle {comprobante_detalle_id} no encontrado")
    return ComprobanteDetalleRead(**row)


async def create_comprobante_detalle(client_id: UUID, data: ComprobanteDetalleCreate) -> ComprobanteDetalleRead:
    """Crea un detalle."""
    row = await _create_comprobante_detalle(client_id, data.model_dump(exclude_none=True))
    return ComprobanteDetalleRead(**row)


async def update_comprobante_detalle(
    client_id: UUID, comprobante_detalle_id: UUID, data: ComprobanteDetalleUpdate
) -> ComprobanteDetalleRead:
    """Actualiza un detalle. Lanza NotFoundError si no existe."""
    row = await _update_comprobante_detalle(
        client_id, comprobante_detalle_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Detalle {comprobante_detalle_id} no encontrado")
    return ComprobanteDetalleRead(**row)
