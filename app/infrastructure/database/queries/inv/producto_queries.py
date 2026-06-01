"""
Queries SQLAlchemy Core para inv_producto.
Filtro tenant estricto: todas las operaciones usan cliente_id.
Aislamiento empresa: get/update/list por empresa_id cuando se provee (INV).
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import InvProductoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.core.tenant.company_scope import empresa_scoped_conditions

_COLUMNS = {c.name for c in InvProductoTable.c}


async def list_productos(
    client_id: UUID,
    empresa_id: UUID,
    categoria_id: Optional[UUID] = None,
    tipo_producto: Optional[str] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lista productos del tenant y empresa."""
    query = select(InvProductoTable).where(
        and_(
            InvProductoTable.c.cliente_id == client_id,
            InvProductoTable.c.empresa_id == empresa_id,
        )
    )
    if categoria_id:
        query = query.where(InvProductoTable.c.categoria_id == categoria_id)
    if tipo_producto:
        query = query.where(InvProductoTable.c.tipo_producto == tipo_producto)
    if solo_activos:
        query = query.where(InvProductoTable.c.es_activo == True)
    if buscar:
        search_filter = or_(
            InvProductoTable.c.nombre.ilike(f"%{buscar}%"),
            InvProductoTable.c.codigo_sku.ilike(f"%{buscar}%"),
            InvProductoTable.c.codigo_barra.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(InvProductoTable.c.nombre)
    return await execute_query(query, client_id=client_id)


async def get_producto_by_id(
    client_id: UUID,
    producto_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Obtiene un producto por id. Con empresa_id: triple filtro (INV)."""
    conds = [
        InvProductoTable.c.cliente_id == client_id,
        InvProductoTable.c.producto_id == producto_id,
    ]
    if empresa_id is not None:
        conds.append(InvProductoTable.c.empresa_id == empresa_id)
    query = select(InvProductoTable).where(and_(*conds))
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def get_producto_by_sku(
    client_id: UUID, empresa_id: UUID, codigo_sku: str
) -> Optional[Dict[str, Any]]:
    """Obtiene un producto por SKU dentro de tenant+empresa (UQ por empresa)."""
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
    empresa_id = payload["empresa_id"]
    stmt = insert(InvProductoTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_producto_by_id(
        client_id, payload["producto_id"], empresa_id=empresa_id
    )


async def update_producto(
    client_id: UUID,
    producto_id: UUID,
    data: Dict[str, Any],
    empresa_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Actualiza un producto. WHERE: cliente_id + empresa_id + producto_id."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _COLUMNS and k not in ("producto_id", "cliente_id", "empresa_id")
    }
    if not payload:
        return await get_producto_by_id(client_id, producto_id, empresa_id=empresa_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(InvProductoTable)
        .where(
            empresa_scoped_conditions(
                InvProductoTable,
                client_id=client_id,
                empresa_id=empresa_id,
                entity_id_column=InvProductoTable.c.producto_id,
                entity_id=producto_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_producto_by_id(client_id, producto_id, empresa_id=empresa_id)
