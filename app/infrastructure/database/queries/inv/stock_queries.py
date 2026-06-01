"""
Queries SQLAlchemy Core para inv_stock.
Filtro tenant estricto: todas las operaciones usan cliente_id.
Aislamiento empresa: get/update/list por empresa_id (INV).
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import InvStockTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.core.tenant.company_scope import empresa_scoped_conditions

_COLUMNS = {c.name for c in InvStockTable.c}


async def list_stocks(
    client_id: UUID,
    empresa_id: UUID,
    producto_id: Optional[UUID] = None,
    almacen_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    """Lista stocks del tenant y empresa."""
    query = select(InvStockTable).where(
        and_(
            InvStockTable.c.cliente_id == client_id,
            InvStockTable.c.empresa_id == empresa_id,
        )
    )
    if producto_id:
        query = query.where(InvStockTable.c.producto_id == producto_id)
    if almacen_id:
        query = query.where(InvStockTable.c.almacen_id == almacen_id)
    query = query.order_by(InvStockTable.c.producto_id, InvStockTable.c.almacen_id)
    return await execute_query(query, client_id=client_id)


async def get_stock_by_id(
    client_id: UUID,
    stock_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Obtiene un stock por id. Con empresa_id: triple filtro (INV)."""
    conds = [
        InvStockTable.c.cliente_id == client_id,
        InvStockTable.c.stock_id == stock_id,
    ]
    if empresa_id is not None:
        conds.append(InvStockTable.c.empresa_id == empresa_id)
    query = select(InvStockTable).where(and_(*conds))
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def get_stock_by_producto_almacen(
    client_id: UUID,
    empresa_id: UUID,
    producto_id: UUID,
    almacen_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Obtiene stock por producto, almacén y empresa."""
    query = select(InvStockTable).where(
        and_(
            InvStockTable.c.cliente_id == client_id,
            InvStockTable.c.empresa_id == empresa_id,
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
    empresa_id = payload["empresa_id"]
    stmt = insert(InvStockTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_stock_by_id(client_id, payload["stock_id"], empresa_id=empresa_id)


async def update_stock(
    client_id: UUID,
    stock_id: UUID,
    data: Dict[str, Any],
    empresa_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Actualiza un stock. WHERE: cliente_id + empresa_id + stock_id."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _COLUMNS and k not in ("stock_id", "cliente_id", "empresa_id")
    }
    if not payload:
        return await get_stock_by_id(client_id, stock_id, empresa_id=empresa_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(InvStockTable)
        .where(
            empresa_scoped_conditions(
                InvStockTable,
                client_id=client_id,
                empresa_id=empresa_id,
                entity_id_column=InvStockTable.c.stock_id,
                entity_id=stock_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_stock_by_id(client_id, stock_id, empresa_id=empresa_id)


async def list_stock_alertas_bajo_minimo(
    client_id: UUID,
    empresa_id: UUID,
    almacen_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    """
    Lista stocks con nivel bajo mínimo para la empresa activa.
    Calcula disponible como: cantidad_actual - cantidad_reservada.
    """
    query = select(InvStockTable).where(
        and_(
            InvStockTable.c.cliente_id == client_id,
            InvStockTable.c.empresa_id == empresa_id,
        )
    )
    if almacen_id:
        query = query.where(InvStockTable.c.almacen_id == almacen_id)
    rows = await execute_query(query, client_id=client_id)
    alerts: List[Dict[str, Any]] = []
    for r in rows:
        actual = Decimal(str(r.get("cantidad_actual") or 0))
        reservada = Decimal(str(r.get("cantidad_reservada") or 0))
        disponible = actual - reservada
        minimo = r.get("stock_minimo")
        if minimo is None:
            continue
        minimo_d = Decimal(str(minimo))
        if disponible < minimo_d:
            rr = dict(r)
            rr["cantidad_disponible"] = disponible
            alerts.append(rr)
    return alerts
