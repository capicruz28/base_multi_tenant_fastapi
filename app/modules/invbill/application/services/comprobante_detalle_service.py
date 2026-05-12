"""
Servicios de aplicación para invbill_comprobante_detalle.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Optional
from uuid import UUID

from app.infrastructure.database.queries.invbill import (
    list_comprobante_detalles as _list_comprobante_detalles,
    get_comprobante_detalle_by_id as _get_comprobante_detalle_by_id,
    create_comprobante_detalle as _create_comprobante_detalle,
    update_comprobante_detalle as _update_comprobante_detalle,
    get_comprobante_by_id as _get_comprobante_by_id,
)
from app.modules.invbill.presentation.schemas import (
    ComprobanteDetalleCreate,
    ComprobanteDetalleUpdate,
    ComprobanteDetalleRead,
)
from app.core.exceptions import NotFoundError, ServiceError


def _estado_norm(val: Optional[str]) -> str:
    return (val or "").strip().lower()


async def _require_comprobante_borrador(client_id: UUID, comprobante_id: UUID) -> None:
    parent = await _get_comprobante_by_id(client_id, comprobante_id)
    if not parent:
        raise NotFoundError(f"Comprobante {comprobante_id} no encontrado")
    if _estado_norm(parent.get("estado")) != "borrador":
        raise ServiceError(
            status_code=400,
            detail="Solo se permiten líneas mientras el comprobante esté en estado borrador.",
            internal_code="INV_BILL_DETALLE_PADRE_NOT_BORRADOR",
        )


async def list_comprobante_detalles(
    client_id: UUID,
    comprobante_id: Optional[UUID] = None,
) -> List[ComprobanteDetalleRead]:
    """Lista detalles de comprobantes del tenant."""
    rows = await _list_comprobante_detalles(
        client_id=client_id,
        comprobante_id=comprobante_id,
    )
    return [ComprobanteDetalleRead(**row) for row in rows]


async def get_comprobante_detalle_by_id(
    client_id: UUID, comprobante_detalle_id: UUID
) -> ComprobanteDetalleRead:
    """Obtiene un detalle por id. Lanza NotFoundError si no existe."""
    row = await _get_comprobante_detalle_by_id(client_id, comprobante_detalle_id)
    if not row:
        raise NotFoundError(f"Detalle {comprobante_detalle_id} no encontrado")
    return ComprobanteDetalleRead(**row)


async def create_comprobante_detalle(
    client_id: UUID, data: ComprobanteDetalleCreate
) -> ComprobanteDetalleRead:
    """Crea un detalle."""
    await _require_comprobante_borrador(client_id, data.comprobante_id)
    row = await _create_comprobante_detalle(client_id, data.model_dump(exclude_none=True))
    return ComprobanteDetalleRead(**row)


async def update_comprobante_detalle(
    client_id: UUID,
    comprobante_detalle_id: UUID,
    data: ComprobanteDetalleUpdate,
) -> ComprobanteDetalleRead:
    """Actualiza un detalle solo si la cabecera está en borrador."""
    row = await _get_comprobante_detalle_by_id(client_id, comprobante_detalle_id)
    if not row:
        raise NotFoundError(f"Detalle {comprobante_detalle_id} no encontrado")
    await _require_comprobante_borrador(client_id, row["comprobante_id"])
    row2 = await _update_comprobante_detalle(
        client_id, comprobante_detalle_id, data.model_dump(exclude_none=True)
    )
    if not row2:
        raise NotFoundError(f"Detalle {comprobante_detalle_id} no encontrado")
    return ComprobanteDetalleRead(**row2)
