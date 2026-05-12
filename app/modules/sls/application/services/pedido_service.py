"""
Servicios de aplicación para sls_pedido.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import date, datetime

from app.infrastructure.database.queries.sls import (
    list_pedidos as _list_pedidos,
    get_pedido_by_id as _get_pedido_by_id,
    create_pedido as _create_pedido,
    update_pedido as _update_pedido,
    list_detalle_by_pedido_id as _list_detalle_by_pedido_id,
    replace_detalle_pedido as _replace_detalle_pedido,
)
from app.modules.sls.presentation.schemas import (
    PedidoCreate,
    PedidoUpdate,
    PedidoRead,
    PedidoDetalleCreate,
    PedidoDetalleRead,
)
from app.core.exceptions import NotFoundError, ServiceError


async def list_pedidos(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    cliente_venta_id: Optional[UUID] = None,
    vendedor_usuario_id: Optional[UUID] = None,
    cotizacion_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> List[PedidoRead]:
    """Lista pedidos del tenant."""
    rows = await _list_pedidos(
        client_id=client_id,
        empresa_id=empresa_id,
        cliente_venta_id=cliente_venta_id,
        vendedor_usuario_id=vendedor_usuario_id,
        cotizacion_id=cotizacion_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )
    return [PedidoRead(**row) for row in rows]


async def get_pedido_by_id(client_id: UUID, pedido_id: UUID) -> PedidoRead:
    """Obtiene un pedido por id. Lanza NotFoundError si no existe."""
    row = await _get_pedido_by_id(client_id, pedido_id)
    if not row:
        raise NotFoundError(f"Pedido {pedido_id} no encontrado")
    return PedidoRead(**row)


async def create_pedido(client_id: UUID, data: PedidoCreate) -> PedidoRead:
    """Crea un pedido."""
    row = await _create_pedido(client_id, data.model_dump(exclude_none=True))
    return PedidoRead(**row)


async def update_pedido(
    client_id: UUID, pedido_id: UUID, data: PedidoUpdate
) -> PedidoRead:
    """Actualiza un pedido. Solo permitido en estado 'borrador'."""
    current = await _get_pedido_by_id(client_id, pedido_id)
    if not current:
        raise NotFoundError(f"Pedido {pedido_id} no encontrado")
    if (current.get("estado") or "").lower() != "borrador":
        raise ServiceError(
            status_code=409,
            detail="El pedido solo puede editarse en estado borrador",
            internal_code="SLS_PEDIDO_NOT_EDITABLE",
        )
    row = await _update_pedido(
        client_id, pedido_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Pedido {pedido_id} no encontrado")
    return PedidoRead(**row)


async def get_detalle_pedido(
    client_id: UUID, pedido_id: UUID
) -> List[PedidoDetalleRead]:
    """Lista el detalle embebido de un pedido."""
    _ = await get_pedido_by_id(client_id, pedido_id)
    rows = await _list_detalle_by_pedido_id(client_id=client_id, pedido_id=pedido_id)
    return [PedidoDetalleRead(**row) for row in rows]


async def put_detalle_pedido(
    client_id: UUID,
    pedido_id: UUID,
    items: List[PedidoDetalleCreate],
) -> List[PedidoDetalleRead]:
    """Reemplaza el detalle completo. Solo permitido en estado 'borrador'."""
    ped = await _get_pedido_by_id(client_id, pedido_id)
    if not ped:
        raise NotFoundError(f"Pedido {pedido_id} no encontrado")
    if (ped.get("estado") or "").lower() != "borrador":
        raise ServiceError(
            status_code=409,
            detail="El detalle solo puede editarse en estado borrador",
            internal_code="SLS_PEDIDO_DET_NOT_EDITABLE",
        )
    empresa_id = ped["empresa_id"]
    payload_items = [i.model_dump(exclude_none=True) for i in items]
    rows = await _replace_detalle_pedido(
        client_id=client_id,
        empresa_id=empresa_id,
        pedido_id=pedido_id,
        items=payload_items,
    )
    return [PedidoDetalleRead(**row) for row in rows]


async def confirmar_pedido(client_id: UUID, pedido_id: UUID) -> PedidoRead:
    ped = await _get_pedido_by_id(client_id, pedido_id)
    if not ped:
        raise NotFoundError(f"Pedido {pedido_id} no encontrado")
    if (ped.get("estado") or "").lower() != "borrador":
        raise ServiceError(409, "Solo se puede confirmar un pedido en borrador", "SLS_PEDIDO_ESTADO_INVALIDO")
    row = await _update_pedido(client_id, pedido_id, {"estado": "confirmado"})
    return PedidoRead(**row)


async def aprobar_pedido(client_id: UUID, pedido_id: UUID, aprobado_por_usuario_id: Optional[UUID] = None) -> PedidoRead:
    ped = await _get_pedido_by_id(client_id, pedido_id)
    if not ped:
        raise NotFoundError(f"Pedido {pedido_id} no encontrado")
    if (ped.get("estado") or "").lower() not in ("confirmado", "borrador"):
        raise ServiceError(409, "Solo se puede aprobar un pedido confirmado", "SLS_PEDIDO_ESTADO_INVALIDO")
    row = await _update_pedido(
        client_id,
        pedido_id,
        {
            "estado": "aprobado",
            "aprobado_por_usuario_id": aprobado_por_usuario_id,
            "fecha_aprobacion": datetime.utcnow(),
        },
    )
    return PedidoRead(**row)


async def anular_pedido(client_id: UUID, pedido_id: UUID, motivo: str | None = None) -> PedidoRead:
    ped = await _get_pedido_by_id(client_id, pedido_id)
    if not ped:
        raise NotFoundError(f"Pedido {pedido_id} no encontrado")
    if (ped.get("estado") or "").lower() == "anulado":
        return PedidoRead(**ped)
    row = await _update_pedido(
        client_id,
        pedido_id,
        {
            "estado": "anulado",
            "motivo_anulacion": motivo,
            "fecha_anulacion": datetime.utcnow(),
        },
    )
    return PedidoRead(**row)
