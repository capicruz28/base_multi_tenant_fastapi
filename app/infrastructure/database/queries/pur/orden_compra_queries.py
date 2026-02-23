"""
Queries SQLAlchemy Core para pur_orden_compra.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, date
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import PurOrdenCompraTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in PurOrdenCompraTable.c}


async def list_ordenes_compra(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    proveedor_id: Optional[UUID] = None,
    solicitud_compra_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> List[Dict[str, Any]]:
    """Lista órdenes de compra del tenant. Siempre filtra por cliente_id."""
    query = select(PurOrdenCompraTable).where(
        PurOrdenCompraTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(PurOrdenCompraTable.c.empresa_id == empresa_id)
    if proveedor_id:
        query = query.where(PurOrdenCompraTable.c.proveedor_id == proveedor_id)
    if solicitud_compra_id:
        query = query.where(PurOrdenCompraTable.c.solicitud_compra_id == solicitud_compra_id)
    if estado:
        query = query.where(PurOrdenCompraTable.c.estado == estado)
    if fecha_desde:
        query = query.where(PurOrdenCompraTable.c.fecha_emision >= fecha_desde)
    if fecha_hasta:
        query = query.where(PurOrdenCompraTable.c.fecha_emision <= fecha_hasta)
    query = query.order_by(PurOrdenCompraTable.c.fecha_emision.desc())
    return await execute_query(query, client_id=client_id)


async def get_orden_compra_by_id(client_id: UUID, orden_compra_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una orden de compra por id. Exige cliente_id para no cruzar tenants."""
    query = select(PurOrdenCompraTable).where(
        and_(
            PurOrdenCompraTable.c.cliente_id == client_id,
            PurOrdenCompraTable.c.orden_compra_id == orden_compra_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_orden_compra(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una orden de compra. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("orden_compra_id", uuid4())
    stmt = insert(PurOrdenCompraTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_orden_compra_by_id(client_id, payload["orden_compra_id"])


async def update_orden_compra(
    client_id: UUID, orden_compra_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una orden de compra. WHERE incluye cliente_id y orden_compra_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("orden_compra_id", "cliente_id")
    }
    if not payload:
        return await get_orden_compra_by_id(client_id, orden_compra_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(PurOrdenCompraTable)
        .where(
            and_(
                PurOrdenCompraTable.c.cliente_id == client_id,
                PurOrdenCompraTable.c.orden_compra_id == orden_compra_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_orden_compra_by_id(client_id, orden_compra_id)
