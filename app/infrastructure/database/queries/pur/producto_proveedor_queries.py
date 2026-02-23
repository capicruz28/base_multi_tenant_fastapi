"""
Queries SQLAlchemy Core para pur_producto_proveedor.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import PurProductoProveedorTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in PurProductoProveedorTable.c}


async def list_productos_proveedor(
    client_id: UUID,
    proveedor_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    solo_activos: bool = True
) -> List[Dict[str, Any]]:
    """Lista productos por proveedor del tenant. Siempre filtra por cliente_id."""
    query = select(PurProductoProveedorTable).where(
        PurProductoProveedorTable.c.cliente_id == client_id
    )
    if proveedor_id:
        query = query.where(PurProductoProveedorTable.c.proveedor_id == proveedor_id)
    if producto_id:
        query = query.where(PurProductoProveedorTable.c.producto_id == producto_id)
    if solo_activos:
        query = query.where(PurProductoProveedorTable.c.es_activo == True)
    query = query.order_by(PurProductoProveedorTable.c.producto_id)
    return await execute_query(query, client_id=client_id)


async def get_producto_proveedor_by_id(client_id: UUID, producto_proveedor_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un producto_proveedor por id. Exige cliente_id para no cruzar tenants."""
    query = select(PurProductoProveedorTable).where(
        and_(
            PurProductoProveedorTable.c.cliente_id == client_id,
            PurProductoProveedorTable.c.producto_proveedor_id == producto_proveedor_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_producto_proveedor(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un producto_proveedor. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("producto_proveedor_id", uuid4())
    stmt = insert(PurProductoProveedorTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_producto_proveedor_by_id(client_id, payload["producto_proveedor_id"])


async def update_producto_proveedor(
    client_id: UUID, producto_proveedor_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un producto_proveedor. WHERE incluye cliente_id y producto_proveedor_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("producto_proveedor_id", "cliente_id")
    }
    if not payload:
        return await get_producto_proveedor_by_id(client_id, producto_proveedor_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(PurProductoProveedorTable)
        .where(
            and_(
                PurProductoProveedorTable.c.cliente_id == client_id,
                PurProductoProveedorTable.c.producto_proveedor_id == producto_proveedor_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_producto_proveedor_by_id(client_id, producto_proveedor_id)
