"""
Servicio de Solicitud de Compra Detalle (PUR). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.modules.org.application.services.empresa_service import get_empresa_servicio
from app.infrastructure.database.queries.pur import (
    list_solicitudes_detalle,
    get_solicitud_detalle_by_id,
    create_solicitud_detalle,
    update_solicitud_detalle,
    get_solicitud_by_id,
)
from app.modules.pur.presentation.schemas import (
    SolicitudCompraDetalleCreate,
    SolicitudCompraDetalleUpdate,
    SolicitudCompraDetalleRead,
)

_EDITABLE_SOLICITUD = frozenset({"borrador", "pendiente_aprobacion"})


def _row_to_read(row: dict) -> SolicitudCompraDetalleRead:
    return SolicitudCompraDetalleRead(**row)

def _norm_estado(value: Optional[str]) -> str:
    return (value or "").strip().lower()


async def _require_solicitud_editable(
    *, client_id: UUID, solicitud_id: UUID, not_found_detail: str
) -> None:
    cab = await get_solicitud_by_id(client_id=client_id, solicitud_id=solicitud_id)
    if not cab:
        raise NotFoundError(detail=not_found_detail)
    if _norm_estado(cab.get("estado")) not in _EDITABLE_SOLICITUD:
        raise ValueError(
            "No se puede modificar el detalle: la solicitud no está en estado editable"
        )


async def list_solicitudes_detalle_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    solicitud_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
) -> List[SolicitudCompraDetalleRead]:
    rows = await list_solicitudes_detalle(
        client_id=client_id,
        empresa_id=empresa_id,
        solicitud_id=solicitud_id,
        producto_id=producto_id,
    )
    return [_row_to_read(r) for r in rows]


async def get_solicitud_detalle_servicio(
    client_id: UUID,
    solicitud_detalle_id: UUID,
) -> SolicitudCompraDetalleRead:
    row = await get_solicitud_detalle_by_id(
        client_id=client_id, solicitud_detalle_id=solicitud_detalle_id
    )
    if not row:
        raise NotFoundError(detail="Detalle de solicitud de compra no encontrado")
    return _row_to_read(row)


async def create_solicitud_detalle_servicio(
    client_id: UUID,
    data: SolicitudCompraDetalleCreate,
) -> SolicitudCompraDetalleRead:
    await get_empresa_servicio(client_id=client_id, empresa_id=data.empresa_id)
    await _require_solicitud_editable(
        client_id=client_id,
        solicitud_id=data.solicitud_id,
        not_found_detail="Solicitud de compra no encontrada",
    )
    payload = data.model_dump()
    row = await create_solicitud_detalle(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_solicitud_detalle_servicio(
    client_id: UUID,
    solicitud_detalle_id: UUID,
    data: SolicitudCompraDetalleUpdate,
) -> SolicitudCompraDetalleRead:
    row = await get_solicitud_detalle_by_id(
        client_id=client_id, solicitud_detalle_id=solicitud_detalle_id
    )
    if not row:
        raise NotFoundError(detail="Detalle de solicitud de compra no encontrado")
    await _require_solicitud_editable(
        client_id=client_id,
        solicitud_id=row["solicitud_id"],
        not_found_detail="Solicitud de compra no encontrada",
    )
    payload = data.model_dump(exclude_unset=True)
    updated = await update_solicitud_detalle(
        client_id=client_id,
        solicitud_detalle_id=solicitud_detalle_id,
        data=payload,
    )
    return _row_to_read(updated)


