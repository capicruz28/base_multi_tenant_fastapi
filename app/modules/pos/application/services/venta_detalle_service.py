"""
Servicios de aplicación para pos_venta_detalle.
"""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError, ValidationError
from app.infrastructure.database.queries.pos import (
    list_venta_detalles as _list_venta_detalles,
    get_venta_detalle_by_id as _get_venta_detalle_by_id,
    create_venta_detalle as _create_venta_detalle,
    update_venta_detalle as _update_venta_detalle,
    get_venta_by_id as _get_venta_by_id,
)
from app.modules.pos.presentation.schemas import (
    VentaDetalleCreate,
    VentaDetalleUpdate,
    VentaDetalleRead,
)

_LINE_EDITABLE = frozenset({"borrador", "pendiente"})


def _norm(val: Optional[str]) -> str:
    return (val or "").strip().lower()


async def _requiere_venta_editable_para_lineas(client_id: UUID, venta_id: UUID) -> None:
    cab = await _get_venta_by_id(client_id, venta_id)
    if not cab:
        raise NotFoundError(f"Venta {venta_id} no encontrada")
    st = _norm(cab.get("estado"))
    if st == "anulada":
        raise ValidationError(
            "La venta está anulada; no se pueden modificar líneas.",
            internal_code="POS_DETALLE_VENTA_ANULADA",
        )
    if st not in _LINE_EDITABLE:
        raise ValidationError(
            "Solo se pueden modificar líneas con la venta en borrador o pendiente.",
            internal_code="POS_DETALLE_VENTA_CERRADA",
        )


async def list_venta_detalles(
    client_id: UUID,
    venta_id: Optional[UUID] = None,
    empresa_id: Optional[UUID] = None,
) -> List[VentaDetalleRead]:
    """Lista detalles de venta POS del tenant."""
    rows = await _list_venta_detalles(
        client_id=client_id, venta_id=venta_id, empresa_id=empresa_id
    )
    return [VentaDetalleRead(**row) for row in rows]


async def get_venta_detalle_by_id(
    client_id: UUID,
    venta_detalle_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> VentaDetalleRead:
    """Obtiene un detalle de venta por id."""
    row = await _get_venta_detalle_by_id(
        client_id, venta_detalle_id, empresa_id=empresa_id
    )
    if not row:
        raise NotFoundError(f"Detalle de venta {venta_detalle_id} no encontrado")
    return VentaDetalleRead(**row)


async def create_venta_detalle(
    client_id: UUID, data: VentaDetalleCreate
) -> VentaDetalleRead:
    """Crea un detalle de venta."""
    await _requiere_venta_editable_para_lineas(client_id, data.venta_id)
    row = await _create_venta_detalle(client_id, data.model_dump(exclude_none=True))
    return VentaDetalleRead(**row)


async def update_venta_detalle(
    client_id: UUID,
    venta_detalle_id: UUID,
    data: VentaDetalleUpdate,
    empresa_id: Optional[UUID] = None,
) -> VentaDetalleRead:
    """Actualiza un detalle de venta."""
    prev = await _get_venta_detalle_by_id(
        client_id, venta_detalle_id, empresa_id=empresa_id
    )
    if not prev:
        raise NotFoundError(f"Detalle de venta {venta_detalle_id} no encontrado")
    await _requiere_venta_editable_para_lineas(client_id, prev["venta_id"])

    row = await _update_venta_detalle(
        client_id,
        venta_detalle_id,
        data.model_dump(exclude_none=True),
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(f"Detalle de venta {venta_detalle_id} no encontrado")
    return VentaDetalleRead(**row)
