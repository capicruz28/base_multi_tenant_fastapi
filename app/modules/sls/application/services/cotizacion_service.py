"""
Servicios de aplicación para sls_cotizacion.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import date

from app.infrastructure.database.queries.sls import (
    list_cotizaciones as _list_cotizaciones,
    get_cotizacion_by_id as _get_cotizacion_by_id,
    create_cotizacion as _create_cotizacion,
    update_cotizacion as _update_cotizacion,
)
from app.modules.sls.presentation.schemas import CotizacionCreate, CotizacionUpdate, CotizacionRead
from app.core.exceptions import NotFoundError


async def list_cotizaciones(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    cliente_venta_id: Optional[UUID] = None,
    vendedor_usuario_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> List[CotizacionRead]:
    """Lista cotizaciones del tenant."""
    rows = await _list_cotizaciones(
        client_id=client_id,
        empresa_id=empresa_id,
        cliente_venta_id=cliente_venta_id,
        vendedor_usuario_id=vendedor_usuario_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )
    return [CotizacionRead(**row) for row in rows]


async def get_cotizacion_by_id(client_id: UUID, cotizacion_id: UUID) -> CotizacionRead:
    """Obtiene una cotizacion por id. Lanza NotFoundError si no existe."""
    row = await _get_cotizacion_by_id(client_id, cotizacion_id)
    if not row:
        raise NotFoundError(f"Cotización {cotizacion_id} no encontrada")
    return CotizacionRead(**row)


async def create_cotizacion(client_id: UUID, data: CotizacionCreate) -> CotizacionRead:
    """Crea una cotizacion."""
    row = await _create_cotizacion(client_id, data.model_dump(exclude_none=True))
    return CotizacionRead(**row)


async def update_cotizacion(
    client_id: UUID, cotizacion_id: UUID, data: CotizacionUpdate
) -> CotizacionRead:
    """Actualiza una cotizacion. Lanza NotFoundError si no existe."""
    row = await _update_cotizacion(
        client_id, cotizacion_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Cotización {cotizacion_id} no encontrada")
    return CotizacionRead(**row)
