# app/modules/pur/application/services/cotizacion_service.py
"""
Servicio de Cotización (PUR). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.exceptions import NotFoundError
from app.modules.org.application.services.empresa_service import get_empresa_servicio
from app.infrastructure.database.queries.pur import (
    list_cotizaciones,
    get_cotizacion_by_id,
    create_cotizacion,
    update_cotizacion,
    clear_es_ganadora_by_solicitud,
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
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    sort_by: Optional[str] = None,
    order: Optional[str] = None,
) -> List[CotizacionRead]:
    skip = (page - 1) * page_size if page is not None and page_size is not None else None
    limit = page_size if page_size is not None else None
    rows = await list_cotizaciones(
        client_id=client_id,
        empresa_id=empresa_id,
        proveedor_id=proveedor_id,
        solicitud_compra_id=solicitud_compra_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        order=order,
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
    await get_empresa_servicio(client_id=client_id, empresa_id=data.empresa_id)
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


async def marcar_ganadora_cotizacion_servicio(
    client_id: UUID,
    cotizacion_id: UUID,
) -> CotizacionRead:
    row = await get_cotizacion_by_id(client_id=client_id, cotizacion_id=cotizacion_id)
    if not row:
        raise NotFoundError(detail="Cotización no encontrada")
    solicitud_compra_id = row.get("solicitud_compra_id")
    if solicitud_compra_id:
        await clear_es_ganadora_by_solicitud(
            client_id=client_id, solicitud_compra_id=solicitud_compra_id
        )
    payload = {"es_ganadora": True}
    updated = await update_cotizacion(
        client_id=client_id, cotizacion_id=cotizacion_id, data=payload
    )
    return _row_to_read(updated)
