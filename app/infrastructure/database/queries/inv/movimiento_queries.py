"""
Queries SQLAlchemy Core para inv_movimiento.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, date
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import InvMovimientoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in InvMovimientoTable.c}


async def list_movimientos(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_movimiento_id: Optional[UUID] = None,
    almacen_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> List[Dict[str, Any]]:
    """Lista movimientos del tenant. Siempre filtra por cliente_id."""
    query = select(InvMovimientoTable).where(
        InvMovimientoTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(InvMovimientoTable.c.empresa_id == empresa_id)
    if tipo_movimiento_id:
        query = query.where(InvMovimientoTable.c.tipo_movimiento_id == tipo_movimiento_id)
    if almacen_id:
        query = query.where(
            (InvMovimientoTable.c.almacen_origen_id == almacen_id) |
            (InvMovimientoTable.c.almacen_destino_id == almacen_id)
        )
    if estado:
        query = query.where(InvMovimientoTable.c.estado == estado)
    if fecha_desde:
        query = query.where(InvMovimientoTable.c.fecha_movimiento >= fecha_desde)
    if fecha_hasta:
        query = query.where(InvMovimientoTable.c.fecha_movimiento <= fecha_hasta)
    query = query.order_by(InvMovimientoTable.c.fecha_movimiento.desc())
    return await execute_query(query, client_id=client_id)


async def get_movimiento_by_id(client_id: UUID, movimiento_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un movimiento por id. Exige cliente_id para no cruzar tenants."""
    query = select(InvMovimientoTable).where(
        and_(
            InvMovimientoTable.c.cliente_id == client_id,
            InvMovimientoTable.c.movimiento_id == movimiento_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_movimiento(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un movimiento. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("movimiento_id", uuid4())
    stmt = insert(InvMovimientoTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_movimiento_by_id(client_id, payload["movimiento_id"])


async def update_movimiento(
    client_id: UUID, movimiento_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un movimiento. WHERE incluye cliente_id y movimiento_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("movimiento_id", "cliente_id")
    }
    if not payload:
        return await get_movimiento_by_id(client_id, movimiento_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(InvMovimientoTable)
        .where(
            and_(
                InvMovimientoTable.c.cliente_id == client_id,
                InvMovimientoTable.c.movimiento_id == movimiento_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_movimiento_by_id(client_id, movimiento_id)
