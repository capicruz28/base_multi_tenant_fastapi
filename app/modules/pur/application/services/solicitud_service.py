# app/modules/pur/application/services/solicitud_service.py
"""
Servicio de Solicitud de Compra (PUR). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime

from app.core.exceptions import NotFoundError
from app.modules.org.application.services.empresa_service import get_empresa_servicio
from app.infrastructure.database.queries.pur import (
    list_solicitudes,
    get_solicitud_by_id,
    create_solicitud,
    update_solicitud,
    list_solicitudes_detalle,
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
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    sort_by: Optional[str] = None,
    order: Optional[str] = None,
) -> List[SolicitudCompraRead]:
    skip = (page - 1) * page_size if page is not None and page_size is not None else None
    limit = page_size if page_size is not None else None
    rows = await list_solicitudes(
        client_id=client_id,
        empresa_id=empresa_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        order=order,
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
    await get_empresa_servicio(client_id=client_id, empresa_id=data.empresa_id)
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


async def aprobar_solicitud_servicio(
    client_id: UUID,
    solicitud_id: UUID,
    aprobado_por_usuario_id: UUID,
) -> SolicitudCompraRead:
    row = await get_solicitud_by_id(client_id=client_id, solicitud_id=solicitud_id)
    if not row:
        raise NotFoundError(detail="Solicitud de compra no encontrada")
    if row.get("estado") not in ("borrador", "pendiente_aprobacion"):
        raise ValueError("Solo se puede aprobar una solicitud en borrador o pendiente de aprobación")

    # Protección adicional: no permitir aprobación sin detalle.
    empresa_id = row.get("empresa_id")
    detalles = await list_solicitudes_detalle(
        client_id=client_id,
        empresa_id=empresa_id,
        solicitud_id=solicitud_id,
    )
    if not detalles:
        raise ValueError("No se puede aprobar una solicitud sin detalle")

    payload = {
        "estado": "aprobada",
        "aprobado_por_usuario_id": aprobado_por_usuario_id,
        "fecha_aprobacion": datetime.utcnow(),
    }
    updated = await update_solicitud(client_id=client_id, solicitud_id=solicitud_id, data=payload)
    return _row_to_read(updated)


async def rechazar_solicitud_servicio(
    client_id: UUID,
    solicitud_id: UUID,
    motivo_rechazo: str,
) -> SolicitudCompraRead:
    row = await get_solicitud_by_id(client_id=client_id, solicitud_id=solicitud_id)
    if not row:
        raise NotFoundError(detail="Solicitud de compra no encontrada")
    if row.get("estado") not in ("borrador", "pendiente_aprobacion"):
        raise ValueError("Solo se puede rechazar una solicitud en borrador o pendiente de aprobación")
    payload = {"estado": "rechazada", "motivo_rechazo": motivo_rechazo or ""}
    updated = await update_solicitud(client_id=client_id, solicitud_id=solicitud_id, data=payload)
    return _row_to_read(updated)


async def marcar_procesada_solicitud_servicio(
    client_id: UUID,
    solicitud_id: UUID,
) -> SolicitudCompraRead:
    row = await get_solicitud_by_id(client_id=client_id, solicitud_id=solicitud_id)
    if not row:
        raise NotFoundError(detail="Solicitud de compra no encontrada")
    payload = {"estado": "procesada", "orden_compra_generada": True}
    updated = await update_solicitud(client_id=client_id, solicitud_id=solicitud_id, data=payload)
    return _row_to_read(updated)
