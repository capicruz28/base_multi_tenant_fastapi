"""
Servicio de Cotización Detalle (PUR). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.modules.org.application.services.empresa_service import get_empresa_servicio
from app.infrastructure.database.queries.pur import (
    list_cotizaciones_detalle,
    get_cotizacion_detalle_by_id,
    create_cotizacion_detalle,
    update_cotizacion_detalle,
)
from app.modules.pur.presentation.schemas import (
    CotizacionDetalleCreate,
    CotizacionDetalleUpdate,
    CotizacionDetalleRead,
)


def _row_to_read(row: dict) -> CotizacionDetalleRead:
    return CotizacionDetalleRead(**row)


async def list_cotizaciones_detalle_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    cotizacion_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
) -> List[CotizacionDetalleRead]:
    rows = await list_cotizaciones_detalle(
        client_id=client_id,
        empresa_id=empresa_id,
        cotizacion_id=cotizacion_id,
        producto_id=producto_id,
    )
    return [_row_to_read(r) for r in rows]


async def get_cotizacion_detalle_servicio(
    client_id: UUID,
    cotizacion_detalle_id: UUID,
) -> CotizacionDetalleRead:
    row = await get_cotizacion_detalle_by_id(
        client_id=client_id, cotizacion_detalle_id=cotizacion_detalle_id
    )
    if not row:
        raise NotFoundError(detail="Detalle de cotización no encontrado")
    return _row_to_read(row)


async def create_cotizacion_detalle_servicio(
    client_id: UUID,
    data: CotizacionDetalleCreate,
) -> CotizacionDetalleRead:
    await get_empresa_servicio(client_id=client_id, empresa_id=data.empresa_id)
    payload = data.model_dump()
    row = await create_cotizacion_detalle(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_cotizacion_detalle_servicio(
    client_id: UUID,
    cotizacion_detalle_id: UUID,
    data: CotizacionDetalleUpdate,
) -> CotizacionDetalleRead:
    row = await get_cotizacion_detalle_by_id(
        client_id=client_id, cotizacion_detalle_id=cotizacion_detalle_id
    )
    if not row:
        raise NotFoundError(detail="Detalle de cotización no encontrado")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_cotizacion_detalle(
        client_id=client_id,
        cotizacion_detalle_id=cotizacion_detalle_id,
        data=payload,
    )
    return _row_to_read(updated)


