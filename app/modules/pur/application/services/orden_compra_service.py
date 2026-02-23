# app/modules/pur/application/services/orden_compra_service.py
"""
Servicio de Orden de Compra (PUR). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.pur import (
    list_ordenes_compra,
    get_orden_compra_by_id,
    create_orden_compra,
    update_orden_compra,
)
from app.modules.pur.presentation.schemas import (
    OrdenCompraCreate,
    OrdenCompraUpdate,
    OrdenCompraRead,
)


def _row_to_read(row: dict) -> OrdenCompraRead:
    return OrdenCompraRead(**row)


async def list_ordenes_compra_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    proveedor_id: Optional[UUID] = None,
    solicitud_compra_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> List[OrdenCompraRead]:
    rows = await list_ordenes_compra(
        client_id=client_id,
        empresa_id=empresa_id,
        proveedor_id=proveedor_id,
        solicitud_compra_id=solicitud_compra_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )
    return [_row_to_read(r) for r in rows]


async def get_orden_compra_servicio(
    client_id: UUID,
    orden_compra_id: UUID,
) -> OrdenCompraRead:
    row = await get_orden_compra_by_id(client_id=client_id, orden_compra_id=orden_compra_id)
    if not row:
        raise NotFoundError(detail="Orden de compra no encontrada")
    return _row_to_read(row)


async def create_orden_compra_servicio(
    client_id: UUID,
    data: OrdenCompraCreate,
) -> OrdenCompraRead:
    payload = data.model_dump()
    row = await create_orden_compra(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_orden_compra_servicio(
    client_id: UUID,
    orden_compra_id: UUID,
    data: OrdenCompraUpdate,
) -> OrdenCompraRead:
    row = await get_orden_compra_by_id(client_id=client_id, orden_compra_id=orden_compra_id)
    if not row:
        raise NotFoundError(detail="Orden de compra no encontrada")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_orden_compra(client_id=client_id, orden_compra_id=orden_compra_id, data=payload)
    return _row_to_read(updated)
