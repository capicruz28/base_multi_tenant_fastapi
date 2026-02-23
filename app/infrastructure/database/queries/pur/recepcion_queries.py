"""
Queries SQLAlchemy Core para pur_recepcion.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, date
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import PurRecepcionTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in PurRecepcionTable.c}


async def list_recepciones(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    orden_compra_id: Optional[UUID] = None,
    proveedor_id: Optional[UUID] = None,
    almacen_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> List[Dict[str, Any]]:
    """Lista recepciones del tenant. Siempre filtra por cliente_id."""
    query = select(PurRecepcionTable).where(
        PurRecepcionTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(PurRecepcionTable.c.empresa_id == empresa_id)
    if orden_compra_id:
        query = query.where(PurRecepcionTable.c.orden_compra_id == orden_compra_id)
    if proveedor_id:
        query = query.where(PurRecepcionTable.c.proveedor_id == proveedor_id)
    if almacen_id:
        query = query.where(PurRecepcionTable.c.almacen_id == almacen_id)
    if estado:
        query = query.where(PurRecepcionTable.c.estado == estado)
    if fecha_desde:
        query = query.where(PurRecepcionTable.c.fecha_recepcion >= fecha_desde)
    if fecha_hasta:
        query = query.where(PurRecepcionTable.c.fecha_recepcion <= fecha_hasta)
    query = query.order_by(PurRecepcionTable.c.fecha_recepcion.desc())
    return await execute_query(query, client_id=client_id)


async def get_recepcion_by_id(client_id: UUID, recepcion_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una recepcion por id. Exige cliente_id para no cruzar tenants."""
    query = select(PurRecepcionTable).where(
        and_(
            PurRecepcionTable.c.cliente_id == client_id,
            PurRecepcionTable.c.recepcion_id == recepcion_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_recepcion(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una recepcion. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("recepcion_id", uuid4())
    stmt = insert(PurRecepcionTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_recepcion_by_id(client_id, payload["recepcion_id"])


async def update_recepcion(
    client_id: UUID, recepcion_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una recepcion. WHERE incluye cliente_id y recepcion_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("recepcion_id", "cliente_id")
    }
    if not payload:
        return await get_recepcion_by_id(client_id, recepcion_id)
    stmt = (
        update(PurRecepcionTable)
        .where(
            and_(
                PurRecepcionTable.c.cliente_id == client_id,
                PurRecepcionTable.c.recepcion_id == recepcion_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_recepcion_by_id(client_id, recepcion_id)
