"""
Queries SQLAlchemy Core para inv_stock.
Filtro tenant estricto: todas las operaciones usan cliente_id.
Aislamiento empresa: get/update/list por empresa_id (INV).
"""
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, insert, update, and_, func

from app.infrastructure.database.tables_erp import InvProductoTable, InvStockTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.core.tenant.company_scope import empresa_scoped_conditions
from app.shared.pagination.query_helpers import apply_erp_pagination, apply_erp_sort, extract_count

if TYPE_CHECKING:
    from app.shared.pagination.params import ErpPaginationParams

_COLUMNS = {c.name for c in InvStockTable.c}

_SORT_COLUMNS_STOCK = frozenset({"cantidad_actual", "stock_minimo", "fecha_actualizacion"})
_SORT_COLUMN_MAP = {
    "cantidad_actual": InvStockTable.c.cantidad_actual,
    "stock_minimo": InvStockTable.c.stock_minimo,
    "fecha_actualizacion": InvStockTable.c.fecha_actualizacion,
}
_DEFAULT_STOCK_ORDER = [
    (InvStockTable.c.producto_id, "asc"),
    (InvStockTable.c.almacen_id, "asc"),
]


def _build_stock_list_conditions(
    client_id: UUID,
    empresa_id: UUID,
    producto_id: Optional[UUID] = None,
    almacen_id: Optional[UUID] = None,
) -> list:
    conditions = [
        InvStockTable.c.cliente_id == client_id,
        InvStockTable.c.empresa_id == empresa_id,
    ]
    if producto_id:
        conditions.append(InvStockTable.c.producto_id == producto_id)
    if almacen_id:
        conditions.append(InvStockTable.c.almacen_id == almacen_id)
    return conditions


def _stock_minimo_efectivo():
    """Mínimo por almacén con fallback al maestro de producto."""
    return func.coalesce(InvStockTable.c.stock_minimo, InvProductoTable.c.stock_minimo)


def _stock_alerta_from_clause():
    return InvStockTable.join(
        InvProductoTable,
        and_(
            InvStockTable.c.producto_id == InvProductoTable.c.producto_id,
            InvStockTable.c.cliente_id == InvProductoTable.c.cliente_id,
            InvStockTable.c.empresa_id == InvProductoTable.c.empresa_id,
        ),
    )


def _build_stock_alerta_conditions(
    client_id: UUID,
    empresa_id: UUID,
    almacen_id: Optional[UUID] = None,
) -> list:
    disponible = InvStockTable.c.cantidad_actual - func.coalesce(
        InvStockTable.c.cantidad_reservada, 0
    )
    minimo_efectivo = _stock_minimo_efectivo()
    conditions = [
        InvStockTable.c.cliente_id == client_id,
        InvStockTable.c.empresa_id == empresa_id,
        minimo_efectivo.isnot(None),
        disponible < minimo_efectivo,
    ]
    if almacen_id:
        conditions.append(InvStockTable.c.almacen_id == almacen_id)
    return conditions


async def count_stocks(
    client_id: UUID,
    empresa_id: UUID,
    producto_id: Optional[UUID] = None,
    almacen_id: Optional[UUID] = None,
) -> int:
    conditions = _build_stock_list_conditions(
        client_id, empresa_id, producto_id, almacen_id
    )
    query = select(func.count()).select_from(InvStockTable).where(and_(*conditions))
    result = await execute_query(query, client_id=client_id)
    return extract_count(result)


async def list_stocks(
    client_id: UUID,
    empresa_id: UUID,
    producto_id: Optional[UUID] = None,
    almacen_id: Optional[UUID] = None,
    pagination: Optional["ErpPaginationParams"] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lista stocks del tenant y empresa."""
    conditions = _build_stock_list_conditions(
        client_id, empresa_id, producto_id, almacen_id
    )
    query = select(InvStockTable).where(and_(*conditions))
    query = apply_erp_sort(
        query,
        allowed_columns=_SORT_COLUMNS_STOCK,
        column_map=_SORT_COLUMN_MAP,
        sort_by=sort_by,
        sort_dir=sort_dir,
        default_order=_DEFAULT_STOCK_ORDER,
        tie_breaker=("stock_id", InvStockTable.c.stock_id),
    )
    if pagination is not None and pagination.is_paginated:
        query = apply_erp_pagination(query, pagination)
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


async def count_stock_alertas_bajo_minimo(
    client_id: UUID,
    empresa_id: UUID,
    almacen_id: Optional[UUID] = None,
) -> int:
    conditions = _build_stock_alerta_conditions(client_id, empresa_id, almacen_id)
    query = (
        select(func.count())
        .select_from(_stock_alerta_from_clause())
        .where(and_(*conditions))
    )
    result = await execute_query(query, client_id=client_id)
    return extract_count(result)


async def list_stock_alertas_bajo_minimo(
    client_id: UUID,
    empresa_id: UUID,
    almacen_id: Optional[UUID] = None,
    pagination: Optional["ErpPaginationParams"] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Lista stocks con nivel bajo mínimo para la empresa activa (filtro SQL).
    disponible = cantidad_actual - cantidad_reservada.
    minimo_efectivo = COALESCE(inv_stock.stock_minimo, inv_producto.stock_minimo).
    """
    conditions = _build_stock_alerta_conditions(client_id, empresa_id, almacen_id)
    query = (
        select(InvStockTable)
        .select_from(_stock_alerta_from_clause())
        .where(and_(*conditions))
    )
    query = apply_erp_sort(
        query,
        allowed_columns=_SORT_COLUMNS_STOCK,
        column_map=_SORT_COLUMN_MAP,
        sort_by=sort_by,
        sort_dir=sort_dir,
        default_order=_DEFAULT_STOCK_ORDER,
        tie_breaker=("stock_id", InvStockTable.c.stock_id),
    )
    if pagination is not None and pagination.is_paginated:
        query = apply_erp_pagination(query, pagination)
    rows = await execute_query(query, client_id=client_id)
    alerts: List[Dict[str, Any]] = []
    for r in rows:
        actual = Decimal(str(r.get("cantidad_actual") or 0))
        reservada = Decimal(str(r.get("cantidad_reservada") or 0))
        rr = dict(r)
        rr["cantidad_disponible"] = actual - reservada
        alerts.append(rr)
    return alerts
