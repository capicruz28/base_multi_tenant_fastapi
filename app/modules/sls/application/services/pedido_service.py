"""
Servicios de aplicación para sls_pedido.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import date

from app.infrastructure.database.queries.sls import (
    list_pedidos as _list_pedidos,
    get_pedido_by_id as _get_pedido_by_id,
    create_pedido as _create_pedido,
    update_pedido as _update_pedido,
)
from app.modules.sls.presentation.schemas import PedidoCreate, PedidoUpdate, PedidoRead
from app.core.exceptions import NotFoundError


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
    """Actualiza un pedido. Lanza NotFoundError si no existe."""
    row = await _update_pedido(
        client_id, pedido_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Pedido {pedido_id} no encontrado")
    return PedidoRead(**row)
