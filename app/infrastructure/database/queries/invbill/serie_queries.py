"""
Queries SQLAlchemy Core para invbill_serie_comprobante.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import InvbillSerieComprobanteTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in InvbillSerieComprobanteTable.c}


async def list_series(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_comprobante: Optional[str] = None,
    solo_activos: bool = True
) -> List[Dict[str, Any]]:
    """Lista series de comprobantes del tenant. Siempre filtra por cliente_id."""
    query = select(InvbillSerieComprobanteTable).where(
        InvbillSerieComprobanteTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(InvbillSerieComprobanteTable.c.empresa_id == empresa_id)
    if tipo_comprobante:
        query = query.where(InvbillSerieComprobanteTable.c.tipo_comprobante == tipo_comprobante)
    if solo_activos:
        query = query.where(InvbillSerieComprobanteTable.c.es_activo == True)
    query = query.order_by(InvbillSerieComprobanteTable.c.tipo_comprobante, InvbillSerieComprobanteTable.c.serie)
    return await execute_query(query, client_id=client_id)


async def get_serie_by_id(client_id: UUID, serie_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una serie por id. Exige cliente_id para no cruzar tenants."""
    query = select(InvbillSerieComprobanteTable).where(
        and_(
            InvbillSerieComprobanteTable.c.cliente_id == client_id,
            InvbillSerieComprobanteTable.c.serie_id == serie_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_serie(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una serie. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("serie_id", uuid4())
    stmt = insert(InvbillSerieComprobanteTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_serie_by_id(client_id, payload["serie_id"])


async def update_serie(
    client_id: UUID, serie_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una serie. WHERE incluye cliente_id y serie_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("serie_id", "cliente_id")
    }
    if not payload:
        return await get_serie_by_id(client_id, serie_id)
    stmt = (
        update(InvbillSerieComprobanteTable)
        .where(
            and_(
                InvbillSerieComprobanteTable.c.cliente_id == client_id,
                InvbillSerieComprobanteTable.c.serie_id == serie_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_serie_by_id(client_id, serie_id)
