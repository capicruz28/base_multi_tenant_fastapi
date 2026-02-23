"""
Queries SQLAlchemy Core para wms_stock_ubicacion.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import WmsStockUbicacionTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in WmsStockUbicacionTable.c}


async def list_stock_ubicaciones(
    client_id: UUID,
    almacen_id: Optional[UUID] = None,
    ubicacion_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    estado_stock: Optional[str] = None,
    lote: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista stock por ubicación del tenant. Siempre filtra por cliente_id."""
    query = select(WmsStockUbicacionTable).where(
        WmsStockUbicacionTable.c.cliente_id == client_id
    )
    if almacen_id:
        query = query.where(WmsStockUbicacionTable.c.almacen_id == almacen_id)
    if ubicacion_id:
        query = query.where(WmsStockUbicacionTable.c.ubicacion_id == ubicacion_id)
    if producto_id:
        query = query.where(WmsStockUbicacionTable.c.producto_id == producto_id)
    if estado_stock:
        query = query.where(WmsStockUbicacionTable.c.estado_stock == estado_stock)
    if lote:
        query = query.where(WmsStockUbicacionTable.c.lote == lote)
    query = query.order_by(WmsStockUbicacionTable.c.fecha_ingreso.desc())
    return await execute_query(query, client_id=client_id)


async def get_stock_ubicacion_by_id(client_id: UUID, stock_ubicacion_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un stock por ubicación por id. Exige cliente_id para no cruzar tenants."""
    query = select(WmsStockUbicacionTable).where(
        and_(
            WmsStockUbicacionTable.c.cliente_id == client_id,
            WmsStockUbicacionTable.c.stock_ubicacion_id == stock_ubicacion_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_stock_ubicacion(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un stock por ubicación. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("stock_ubicacion_id", uuid4())
    stmt = insert(WmsStockUbicacionTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_stock_ubicacion_by_id(client_id, payload["stock_ubicacion_id"])


async def update_stock_ubicacion(
    client_id: UUID, stock_ubicacion_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un stock por ubicación. WHERE incluye cliente_id y stock_ubicacion_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("stock_ubicacion_id", "cliente_id")
    }
    if not payload:
        return await get_stock_ubicacion_by_id(client_id, stock_ubicacion_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(WmsStockUbicacionTable)
        .where(
            and_(
                WmsStockUbicacionTable.c.cliente_id == client_id,
                WmsStockUbicacionTable.c.stock_ubicacion_id == stock_ubicacion_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_stock_ubicacion_by_id(client_id, stock_ubicacion_id)
