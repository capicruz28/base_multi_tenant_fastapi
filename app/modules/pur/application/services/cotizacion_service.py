# app/modules/pur/application/services/cotizacion_service.py
"""
Servicio de Cotización (PUR). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.pur import (
    list_cotizaciones,
    get_cotizacion_by_id,
    create_cotizacion,
    update_cotizacion,
)
from app.modules.pur.presentation.schemas import (
    CotizacionCreate,
    CotizacionUpdate,
    CotizacionRead,
)


def _row_to_read(row: dict) -> CotizacionRead:
    return CotizacionRead(**row)


async def list_cotizaciones_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    proveedor_id: Optional[UUID] = None,
    solicitud_compra_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> List[CotizacionRead]:
    rows = await list_cotizaciones(
        client_id=client_id,
        empresa_id=empresa_id,
        proveedor_id=proveedor_id,
        solicitud_compra_id=solicitud_compra_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )
    return [_row_to_read(r) for r in rows]


async def get_cotizacion_servicio(
    client_id: UUID,
    cotizacion_id: UUID,
) -> CotizacionRead:
    row = await get_cotizacion_by_id(client_id=client_id, cotizacion_id=cotizacion_id)
    if not row:
        raise NotFoundError(detail="Cotización no encontrada")
    return _row_to_read(row)


async def create_cotizacion_servicio(
    client_id: UUID,
    data: CotizacionCreate,
) -> CotizacionRead:
    payload = data.model_dump()
    row = await create_cotizacion(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_cotizacion_servicio(
    client_id: UUID,
    cotizacion_id: UUID,
    data: CotizacionUpdate,
) -> CotizacionRead:
    row = await get_cotizacion_by_id(client_id=client_id, cotizacion_id=cotizacion_id)
    if not row:
        raise NotFoundError(detail="Cotización no encontrada")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_cotizacion(client_id=client_id, cotizacion_id=cotizacion_id, data=payload)
    return _row_to_read(updated)
