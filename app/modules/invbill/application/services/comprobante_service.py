"""
Servicios de aplicación para invbill_comprobante.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.infrastructure.database.queries.invbill import (
    list_comprobantes as _list_comprobantes,
    get_comprobante_by_id as _get_comprobante_by_id,
    create_comprobante as _create_comprobante,
    update_comprobante as _update_comprobante,
    anular_comprobante as _anular_comprobante,
    procesar_comprobante as _procesar_comprobante,
)
from app.modules.invbill.presentation.schemas import ComprobanteCreate, ComprobanteUpdate, ComprobanteRead
from app.core.exceptions import NotFoundError, ServiceError


def _estado_norm(val: Optional[str]) -> str:
    return (val or "").strip().lower()


async def list_comprobantes(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_comprobante: Optional[str] = None,
    cliente_venta_id: Optional[UUID] = None,
    pedido_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    estado_sunat: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> List[ComprobanteRead]:
    """Lista comprobantes del tenant."""
    rows = await _list_comprobantes(
        client_id=client_id,
        empresa_id=empresa_id,
        tipo_comprobante=tipo_comprobante,
        cliente_venta_id=cliente_venta_id,
        pedido_id=pedido_id,
        estado=estado,
        estado_sunat=estado_sunat,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return [ComprobanteRead(**row) for row in rows]


async def get_comprobante_by_id(
    client_id: UUID,
    comprobante_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> ComprobanteRead:
    """Obtiene un comprobante por id. Lanza NotFoundError si no existe."""
    row = await _get_comprobante_by_id(client_id, comprobante_id, empresa_id)
    if not row:
        raise NotFoundError(f"Comprobante {comprobante_id} no encontrado")
    return ComprobanteRead(**row)


async def create_comprobante(client_id: UUID, data: ComprobanteCreate) -> ComprobanteRead:
    """Crea un comprobante."""
    row = await _create_comprobante(client_id, data.model_dump(exclude_none=True))
    return ComprobanteRead(**row)


async def update_comprobante(
    client_id: UUID,
    comprobante_id: UUID,
    data: ComprobanteUpdate,
    empresa_id: Optional[UUID] = None,
) -> ComprobanteRead:
    """Actualiza un comprobante solo en estado borrador. Lanza NotFoundError si no existe."""
    existing = await _get_comprobante_by_id(client_id, comprobante_id, empresa_id)
    if not existing:
        raise NotFoundError(f"Comprobante {comprobante_id} no encontrado")
    if _estado_norm(existing.get("estado")) != "borrador":
        raise ServiceError(
            status_code=400,
            detail="Solo se permite actualizar comprobantes en estado borrador.",
            internal_code="INV_BILL_NOT_BORRADOR",
        )
    row = await _update_comprobante(
        client_id,
        comprobante_id,
        data.model_dump(exclude_none=True),
        empresa_id,
    )
    if not row:
        raise NotFoundError(f"Comprobante {comprobante_id} no encontrado")
    return ComprobanteRead(**row)


async def anular_comprobante(
    client_id: UUID,
    comprobante_id: UUID,
    motivo_anulacion: str,
    empresa_id: Optional[UUID] = None,
) -> ComprobanteRead:
    """Anula comprobante (cualquier estado distinto de anulado)."""
    existing = await _get_comprobante_by_id(client_id, comprobante_id, empresa_id)
    if not existing:
        raise NotFoundError(f"Comprobante {comprobante_id} no encontrado")
    if _estado_norm(existing.get("estado")) == "anulado":
        raise ServiceError(
            status_code=400,
            detail="El comprobante ya está anulado.",
            internal_code="INV_BILL_YA_ANULADO",
        )
    row = await _anular_comprobante(
        client_id, comprobante_id, motivo_anulacion, empresa_id
    )
    if not row:
        raise ServiceError(
            status_code=400,
            detail="No se pudo anular el comprobante.",
            internal_code="INV_BILL_ANULAR_FAILED",
        )
    return ComprobanteRead(**row)


async def procesar_comprobante(
    client_id: UUID,
    comprobante_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> ComprobanteRead:
    """Pasa de borrador a emitido (sin llamada SUNAT en esta fase)."""
    existing = await _get_comprobante_by_id(client_id, comprobante_id, empresa_id)
    if not existing:
        raise NotFoundError(f"Comprobante {comprobante_id} no encontrado")
    if _estado_norm(existing.get("estado")) != "borrador":
        raise ServiceError(
            status_code=400,
            detail="Solo se puede procesar un comprobante en estado borrador.",
            internal_code="INV_BILL_NOT_BORRADOR_PROCESAR",
        )
    row = await _procesar_comprobante(client_id, comprobante_id, empresa_id)
    if not row:
        raise ServiceError(
            status_code=400,
            detail="No se pudo procesar el comprobante.",
            internal_code="INV_BILL_PROCESAR_FAILED",
        )
    return ComprobanteRead(**row)
