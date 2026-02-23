"""
Queries SQLAlchemy Core para inv_stock.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import InvStockTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in InvStockTable.c}


async def list_stocks(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    almacen_id: Optional[UUID] = None
) -> List[Dict[str, Any]]:
    """Lista stocks del tenant. Siempre filtra por cliente_id."""
    query = select(InvStockTable).where(
        InvStockTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(InvStockTable.c.empresa_id == empresa_id)
    if producto_id:
        query = query.where(InvStockTable.c.producto_id == producto_id)
    if almacen_id:
        query = query.where(InvStockTable.c.almacen_id == almacen_id)
    query = query.order_by(InvStockTable.c.producto_id, InvStockTable.c.almacen_id)
    return await execute_query(query, client_id=client_id)


async def get_stock_by_id(client_id: UUID, stock_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un stock por id. Exige cliente_id para no cruzar tenants."""
    query = select(InvStockTable).where(
        and_(
            InvStockTable.c.cliente_id == client_id,
            InvStockTable.c.stock_id == stock_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def get_stock_by_producto_almacen(
    client_id: UUID, producto_id: UUID, almacen_id: UUID
) -> Optional[Dict[str, Any]]:
    """Obtiene stock por producto y almacén. Útil para consultas rápidas."""
    query = select(InvStockTable).where(
        and_(
            InvStockTable.c.cliente_id == client_id,
            InvStockTable.c.producto_id == producto_id,
            InvStockTable.c.almacen_id == almacen_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_stock(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un stock. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("stock_id", uuid4())
    stmt = insert(InvStockTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_stock_by_id(client_id, payload["stock_id"])


async def update_stock(
    client_id: UUID, stock_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un stock. WHERE incluye cliente_id y stock_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("stock_id", "cliente_id")
    }
    if not payload:
        return await get_stock_by_id(client_id, stock_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(InvStockTable)
        .where(
            and_(
                InvStockTable.c.cliente_id == client_id,
                InvStockTable.c.stock_id == stock_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_stock_by_id(client_id, stock_id)
