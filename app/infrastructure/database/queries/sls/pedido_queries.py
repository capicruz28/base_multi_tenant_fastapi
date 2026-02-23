"""
Queries SQLAlchemy Core para sls_pedido.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, date
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import SlsPedidoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in SlsPedidoTable.c}


async def list_pedidos(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    cliente_venta_id: Optional[UUID] = None,
    vendedor_usuario_id: Optional[UUID] = None,
    cotizacion_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> List[Dict[str, Any]]:
    """Lista pedidos del tenant. Siempre filtra por cliente_id."""
    query = select(SlsPedidoTable).where(
        SlsPedidoTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(SlsPedidoTable.c.empresa_id == empresa_id)
    if cliente_venta_id:
        query = query.where(SlsPedidoTable.c.cliente_venta_id == cliente_venta_id)
    if vendedor_usuario_id:
        query = query.where(SlsPedidoTable.c.vendedor_usuario_id == vendedor_usuario_id)
    if cotizacion_id:
        query = query.where(SlsPedidoTable.c.cotizacion_id == cotizacion_id)
    if estado:
        query = query.where(SlsPedidoTable.c.estado == estado)
    if fecha_desde:
        query = query.where(SlsPedidoTable.c.fecha_pedido >= fecha_desde)
    if fecha_hasta:
        query = query.where(SlsPedidoTable.c.fecha_pedido <= fecha_hasta)
    query = query.order_by(SlsPedidoTable.c.fecha_pedido.desc())
    return await execute_query(query, client_id=client_id)


async def get_pedido_by_id(client_id: UUID, pedido_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un pedido por id. Exige cliente_id para no cruzar tenants."""
    query = select(SlsPedidoTable).where(
        and_(
            SlsPedidoTable.c.cliente_id == client_id,
            SlsPedidoTable.c.pedido_id == pedido_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_pedido(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un pedido. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("pedido_id", uuid4())
    stmt = insert(SlsPedidoTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_pedido_by_id(client_id, payload["pedido_id"])


async def update_pedido(
    client_id: UUID, pedido_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un pedido. WHERE incluye cliente_id y pedido_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("pedido_id", "cliente_id")
    }
    if not payload:
        return await get_pedido_by_id(client_id, pedido_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(SlsPedidoTable)
        .where(
            and_(
                SlsPedidoTable.c.cliente_id == client_id,
                SlsPedidoTable.c.pedido_id == pedido_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_pedido_by_id(client_id, pedido_id)
