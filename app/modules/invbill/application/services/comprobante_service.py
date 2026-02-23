"""
Servicios de aplicación para invbill_comprobante.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import date

from app.infrastructure.database.queries.invbill import (
    list_comprobantes as _list_comprobantes,
    get_comprobante_by_id as _get_comprobante_by_id,
    create_comprobante as _create_comprobante,
    update_comprobante as _update_comprobante,
)
from app.modules.invbill.presentation.schemas import ComprobanteCreate, ComprobanteUpdate, ComprobanteRead
from app.core.exceptions import NotFoundError


async def list_comprobantes(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_comprobante: Optional[str] = None,
    cliente_venta_id: Optional[UUID] = None,
    pedido_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    estado_sunat: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> List[ComprobanteRead]:
    """Lista comprobantes del tenant."""
    rows = await _list_comprobantes(
        client_id=client_id,
        empresa_id=empresa_id,
        tipo_comprobante=tipo_comprobante,
        cliente_venta_id=cliente_venta_id,
        pedido_id=pedido_id,
        estado=estado,
        estado_sunat=estado_sunat,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )
    return [ComprobanteRead(**row) for row in rows]


async def get_comprobante_by_id(client_id: UUID, comprobante_id: UUID) -> ComprobanteRead:
    """Obtiene un comprobante por id. Lanza NotFoundError si no existe."""
    row = await _get_comprobante_by_id(client_id, comprobante_id)
    if not row:
        raise NotFoundError(f"Comprobante {comprobante_id} no encontrado")
    return ComprobanteRead(**row)


async def create_comprobante(client_id: UUID, data: ComprobanteCreate) -> ComprobanteRead:
    """Crea un comprobante."""
    row = await _create_comprobante(client_id, data.model_dump(exclude_none=True))
    return ComprobanteRead(**row)


async def update_comprobante(
    client_id: UUID, comprobante_id: UUID, data: ComprobanteUpdate
) -> ComprobanteRead:
    """Actualiza un comprobante. Lanza NotFoundError si no existe."""
    row = await _update_comprobante(
        client_id, comprobante_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Comprobante {comprobante_id} no encontrado")
    return ComprobanteRead(**row)
