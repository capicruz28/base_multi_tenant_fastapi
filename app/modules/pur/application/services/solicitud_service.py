# app/modules/pur/application/services/solicitud_service.py
"""
Servicio de Solicitud de Compra (PUR). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.pur import (
    list_solicitudes,
    get_solicitud_by_id,
    create_solicitud,
    update_solicitud,
)
from app.modules.pur.presentation.schemas import (
    SolicitudCompraCreate,
    SolicitudCompraUpdate,
    SolicitudCompraRead,
)


def _row_to_read(row: dict) -> SolicitudCompraRead:
    return SolicitudCompraRead(**row)


async def list_solicitudes_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> List[SolicitudCompraRead]:
    rows = await list_solicitudes(
        client_id=client_id,
        empresa_id=empresa_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )
    return [_row_to_read(r) for r in rows]


async def get_solicitud_servicio(
    client_id: UUID,
    solicitud_id: UUID,
) -> SolicitudCompraRead:
    row = await get_solicitud_by_id(client_id=client_id, solicitud_id=solicitud_id)
    if not row:
        raise NotFoundError(detail="Solicitud de compra no encontrada")
    return _row_to_read(row)


async def create_solicitud_servicio(
    client_id: UUID,
    data: SolicitudCompraCreate,
) -> SolicitudCompraRead:
    payload = data.model_dump()
    row = await create_solicitud(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_solicitud_servicio(
    client_id: UUID,
    solicitud_id: UUID,
    data: SolicitudCompraUpdate,
) -> SolicitudCompraRead:
    row = await get_solicitud_by_id(client_id=client_id, solicitud_id=solicitud_id)
    if not row:
        raise NotFoundError(detail="Solicitud de compra no encontrada")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_solicitud(client_id=client_id, solicitud_id=solicitud_id, data=payload)
    return _row_to_read(updated)
