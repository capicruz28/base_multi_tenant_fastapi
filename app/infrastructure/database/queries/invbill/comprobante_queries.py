"""
Queries SQLAlchemy Core para invbill_comprobante.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, date
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import InvbillComprobanteTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in InvbillComprobanteTable.c}


async def list_comprobantes(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_comprobante: Optional[str] = None,
    cliente_venta_id: Optional[UUID] = None,
    pedido_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    estado_sunat: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> List[Dict[str, Any]]:
    """Lista comprobantes del tenant. Siempre filtra por cliente_id."""
    query = select(InvbillComprobanteTable).where(
        InvbillComprobanteTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(InvbillComprobanteTable.c.empresa_id == empresa_id)
    if tipo_comprobante:
        query = query.where(InvbillComprobanteTable.c.tipo_comprobante == tipo_comprobante)
    if cliente_venta_id:
        query = query.where(InvbillComprobanteTable.c.cliente_venta_id == cliente_venta_id)
    if pedido_id:
        query = query.where(InvbillComprobanteTable.c.pedido_id == pedido_id)
    if estado:
        query = query.where(InvbillComprobanteTable.c.estado == estado)
    if estado_sunat:
        query = query.where(InvbillComprobanteTable.c.estado_sunat == estado_sunat)
    if fecha_desde:
        query = query.where(InvbillComprobanteTable.c.fecha_emision >= fecha_desde)
    if fecha_hasta:
        query = query.where(InvbillComprobanteTable.c.fecha_emision <= fecha_hasta)
    query = query.order_by(InvbillComprobanteTable.c.fecha_emision.desc())
    return await execute_query(query, client_id=client_id)


async def get_comprobante_by_id(client_id: UUID, comprobante_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un comprobante por id. Exige cliente_id para no cruzar tenants."""
    query = select(InvbillComprobanteTable).where(
        and_(
            InvbillComprobanteTable.c.cliente_id == client_id,
            InvbillComprobanteTable.c.comprobante_id == comprobante_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_comprobante(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un comprobante. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("comprobante_id", uuid4())
    stmt = insert(InvbillComprobanteTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_comprobante_by_id(client_id, payload["comprobante_id"])


async def update_comprobante(
    client_id: UUID, comprobante_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un comprobante. WHERE incluye cliente_id y comprobante_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("comprobante_id", "cliente_id")
    }
    if not payload:
        return await get_comprobante_by_id(client_id, comprobante_id)
    stmt = (
        update(InvbillComprobanteTable)
        .where(
            and_(
                InvbillComprobanteTable.c.cliente_id == client_id,
                InvbillComprobanteTable.c.comprobante_id == comprobante_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_comprobante_by_id(client_id, comprobante_id)
