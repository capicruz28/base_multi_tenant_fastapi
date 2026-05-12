"""
Servicios de aplicación para pos_venta.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.core.exceptions import NotFoundError, ValidationError
from app.infrastructure.database.queries.pos import (
    list_ventas as _list_ventas,
    get_venta_by_id as _get_venta_by_id,
    create_venta as _create_venta,
    update_venta as _update_venta,
    set_venta_anulada as _set_venta_anulada,
)
from app.modules.pos.presentation.schemas import (
    VentaCreate,
    VentaUpdate,
    VentaRead,
    VentaAnularRequest,
)

_EDITABLE = frozenset({"borrador", "pendiente"})
_ANULABLE = frozenset({"borrador", "pendiente", "completada"})


def _norm_estado(val: Optional[str]) -> str:
    return (val or "").strip().lower()


async def list_ventas(
    client_id: UUID,
    punto_venta_id: Optional[UUID] = None,
    turno_caja_id: Optional[UUID] = None,
    empresa_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
) -> List[VentaRead]:
    """Lista ventas POS del tenant."""
    rows = await _list_ventas(
        client_id=client_id,
        punto_venta_id=punto_venta_id,
        turno_caja_id=turno_caja_id,
        empresa_id=empresa_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return [VentaRead(**row) for row in rows]


async def get_venta_by_id(
    client_id: UUID,
    venta_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> VentaRead:
    """Obtiene una venta POS por id."""
    row = await _get_venta_by_id(client_id, venta_id, empresa_id=empresa_id)
    if not row:
        raise NotFoundError(f"Venta {venta_id} no encontrada")
    return VentaRead(**row)


async def create_venta(client_id: UUID, data: VentaCreate) -> VentaRead:
    """Crea una venta POS."""
    row = await _create_venta(client_id, data.model_dump(exclude_none=True))
    return VentaRead(**row)


async def update_venta(
    client_id: UUID,
    venta_id: UUID,
    data: VentaUpdate,
    empresa_id: Optional[UUID] = None,
) -> VentaRead:
    """Actualiza una venta POS solo en estados editables (borrador o pendiente)."""
    raw = data.model_dump(exclude_none=True)
    if raw.get("motivo_anulacion") is not None or raw.get("fecha_anulacion") is not None:
        raise ValidationError(
            "Para anular use POST /ventas/{id}/anular con el motivo.",
            internal_code="POS_VENTA_USE_ANULAR",
        )
    if raw.get("estado") == "anulada":
        raise ValidationError(
            "Para anular use POST /ventas/{id}/anular con el motivo.",
            internal_code="POS_VENTA_USE_ANULAR",
        )

    current = await _get_venta_by_id(client_id, venta_id, empresa_id=empresa_id)
    if not current:
        raise NotFoundError(f"Venta {venta_id} no encontrada")
    st = _norm_estado(current.get("estado"))
    if st not in _EDITABLE:
        raise ValidationError(
            "Solo se puede editar una venta en estado borrador o pendiente.",
            internal_code="POS_VENTA_NO_EDITABLE",
        )

    payload = data.model_dump(exclude_none=True)
    payload.pop("fecha_anulacion", None)
    payload.pop("motivo_anulacion", None)
    if payload.get("estado") == "anulada":
        raise ValidationError(
            "Para anular use POST /ventas/{id}/anular.",
            internal_code="POS_VENTA_USE_ANULAR",
        )

    row = await _update_venta(client_id, venta_id, payload, empresa_id=empresa_id)
    if not row:
        raise NotFoundError(f"Venta {venta_id} no encontrada")
    return VentaRead(**row)


async def anular_venta(
    client_id: UUID,
    venta_id: UUID,
    data: VentaAnularRequest,
    empresa_id: Optional[UUID] = None,
) -> VentaRead:
    """Anula una venta si el estado previo lo permite."""
    current = await _get_venta_by_id(client_id, venta_id, empresa_id=empresa_id)
    if not current:
        raise NotFoundError(f"Venta {venta_id} no encontrada")
    st = _norm_estado(current.get("estado"))
    if st == "anulada":
        raise ValidationError("La venta ya está anulada.", internal_code="POS_VENTA_YA_ANULADA")
    if st not in _ANULABLE:
        raise ValidationError(
            "El estado actual no permite anulación.",
            internal_code="POS_VENTA_NO_ANULABLE",
        )
    row = await _set_venta_anulada(
        client_id,
        venta_id,
        data.motivo_anulacion.strip(),
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(f"Venta {venta_id} no encontrada")
    return VentaRead(**row)
