"""
Queries SQLAlchemy Core para inv_producto.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import InvProductoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in InvProductoTable.c}


async def list_productos(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    categoria_id: Optional[UUID] = None,
    tipo_producto: Optional[str] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista productos del tenant. Siempre filtra por cliente_id."""
    query = select(InvProductoTable).where(
        InvProductoTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(InvProductoTable.c.empresa_id == empresa_id)
    if categoria_id:
        query = query.where(InvProductoTable.c.categoria_id == categoria_id)
    if tipo_producto:
        query = query.where(InvProductoTable.c.tipo_producto == tipo_producto)
    if solo_activos:
        query = query.where(InvProductoTable.c.es_activo == True)
    if buscar:
        # Búsqueda por nombre, SKU o código de barras
        search_filter = or_(
            InvProductoTable.c.nombre.ilike(f"%{buscar}%"),
            InvProductoTable.c.codigo_sku.ilike(f"%{buscar}%"),
            InvProductoTable.c.codigo_barra.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(InvProductoTable.c.nombre)
    return await execute_query(query, client_id=client_id)


async def get_producto_by_id(client_id: UUID, producto_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un producto por id. Exige cliente_id para no cruzar tenants."""
    query = select(InvProductoTable).where(
        and_(
            InvProductoTable.c.cliente_id == client_id,
            InvProductoTable.c.producto_id == producto_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def get_producto_by_sku(client_id: UUID, empresa_id: UUID, codigo_sku: str) -> Optional[Dict[str, Any]]:
    """Obtiene un producto por SKU. Útil para validaciones."""
    query = select(InvProductoTable).where(
        and_(
            InvProductoTable.c.cliente_id == client_id,
            InvProductoTable.c.empresa_id == empresa_id,
            InvProductoTable.c.codigo_sku == codigo_sku,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_producto(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un producto. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("producto_id", uuid4())
    stmt = insert(InvProductoTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_producto_by_id(client_id, payload["producto_id"])


async def update_producto(
    client_id: UUID, producto_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un producto. WHERE incluye cliente_id y producto_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("producto_id", "cliente_id")
    }
    if not payload:
        return await get_producto_by_id(client_id, producto_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(InvProductoTable)
        .where(
            and_(
                InvProductoTable.c.cliente_id == client_id,
                InvProductoTable.c.producto_id == producto_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_producto_by_id(client_id, producto_id)
