"""
Servicio de Orden de Compra Detalle (PUR). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.modules.org.application.services.empresa_service import get_empresa_servicio
from app.infrastructure.database.queries.pur import (
    list_ordenes_compra_detalle,
    get_orden_compra_detalle_by_id,
    create_orden_compra_detalle,
    update_orden_compra_detalle,
)
from app.modules.pur.presentation.schemas import (
    OrdenCompraDetalleCreate,
    OrdenCompraDetalleUpdate,
    OrdenCompraDetalleRead,
)


def _row_to_read(row: dict) -> OrdenCompraDetalleRead:
    return OrdenCompraDetalleRead(**row)


async def list_ordenes_compra_detalle_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    orden_compra_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
) -> List[OrdenCompraDetalleRead]:
    rows = await list_ordenes_compra_detalle(
        client_id=client_id,
        empresa_id=empresa_id,
        orden_compra_id=orden_compra_id,
        producto_id=producto_id,
    )
    return [_row_to_read(r) for r in rows]


async def get_orden_compra_detalle_servicio(
    client_id: UUID,
    orden_compra_detalle_id: UUID,
) -> OrdenCompraDetalleRead:
    row = await get_orden_compra_detalle_by_id(
        client_id=client_id,
        orden_compra_detalle_id=orden_compra_detalle_id,
    )
    if not row:
        raise NotFoundError(detail="Detalle de orden de compra no encontrado")
    return _row_to_read(row)


async def create_orden_compra_detalle_servicio(
    client_id: UUID,
    data: OrdenCompraDetalleCreate,
) -> OrdenCompraDetalleRead:
    await get_empresa_servicio(client_id=client_id, empresa_id=data.empresa_id)
    payload = data.model_dump()
    row = await create_orden_compra_detalle(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_orden_compra_detalle_servicio(
    client_id: UUID,
    orden_compra_detalle_id: UUID,
    data: OrdenCompraDetalleUpdate,
) -> OrdenCompraDetalleRead:
    row = await get_orden_compra_detalle_by_id(
        client_id=client_id,
        orden_compra_detalle_id=orden_compra_detalle_id,
    )
    if not row:
        raise NotFoundError(detail="Detalle de orden de compra no encontrado")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_orden_compra_detalle(
        client_id=client_id,
        orden_compra_detalle_id=orden_compra_detalle_id,
        data=payload,
    )
    return _row_to_read(updated)
