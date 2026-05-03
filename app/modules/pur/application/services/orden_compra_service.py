# app/modules/pur/application/services/orden_compra_service.py
"""
Servicio de Orden de Compra (PUR). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime

from app.core.exceptions import NotFoundError
from app.modules.org.application.services.empresa_service import get_empresa_servicio
from app.infrastructure.database.queries.pur import (
    list_ordenes_compra,
    get_orden_compra_by_id,
    create_orden_compra,
    update_orden_compra,
    list_ordenes_compra_detalle,
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
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    sort_by: Optional[str] = None,
    order: Optional[str] = None,
) -> List[OrdenCompraRead]:
    skip = (page - 1) * page_size if page is not None and page_size is not None else None
    limit = page_size if page_size is not None else None
    rows = await list_ordenes_compra(
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
    await get_empresa_servicio(client_id=client_id, empresa_id=data.empresa_id)
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


async def aprobar_orden_compra_servicio(
    client_id: UUID,
    orden_compra_id: UUID,
    aprobado_por_usuario_id: UUID,
) -> OrdenCompraRead:
    row = await get_orden_compra_by_id(client_id=client_id, orden_compra_id=orden_compra_id)
    if not row:
        raise NotFoundError(detail="Orden de compra no encontrada")
    if row.get("estado") != "borrador":
        raise ValueError("Solo se puede aprobar una orden de compra en estado borrador")

    # Protección adicional: no permitir aprobación sin detalle.
    empresa_id = row.get("empresa_id")
    detalles = await list_ordenes_compra_detalle(
        client_id=client_id,
        empresa_id=empresa_id,
        orden_compra_id=orden_compra_id,
    )
    if not detalles:
        raise ValueError("No se puede aprobar una orden de compra sin detalle")

    payload = {
        "estado": "aprobada",
        "aprobado_por_usuario_id": aprobado_por_usuario_id,
        "fecha_aprobacion": datetime.utcnow(),
    }
    updated = await update_orden_compra(
        client_id=client_id, orden_compra_id=orden_compra_id, data=payload
    )
    return _row_to_read(updated)


async def anular_orden_compra_servicio(
    client_id: UUID,
    orden_compra_id: UUID,
    motivo_anulacion: str,
) -> OrdenCompraRead:
    row = await get_orden_compra_by_id(client_id=client_id, orden_compra_id=orden_compra_id)
    if not row:
        raise NotFoundError(detail="Orden de compra no encontrada")
    payload = {"estado": "anulada", "motivo_anulacion": motivo_anulacion or ""}
    updated = await update_orden_compra(
        client_id=client_id, orden_compra_id=orden_compra_id, data=payload
    )
    return _row_to_read(updated)
