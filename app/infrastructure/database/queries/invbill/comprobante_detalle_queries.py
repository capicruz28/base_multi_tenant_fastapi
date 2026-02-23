"""
Queries SQLAlchemy Core para invbill_comprobante_detalle.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import InvbillComprobanteDetalleTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in InvbillComprobanteDetalleTable.c}


async def list_comprobante_detalles(
    client_id: UUID,
    comprobante_id: Optional[UUID] = None
) -> List[Dict[str, Any]]:
    """Lista detalles de comprobantes del tenant. Siempre filtra por cliente_id."""
    query = select(InvbillComprobanteDetalleTable).where(
        InvbillComprobanteDetalleTable.c.cliente_id == client_id
    )
    if comprobante_id:
        query = query.where(InvbillComprobanteDetalleTable.c.comprobante_id == comprobante_id)
    query = query.order_by(InvbillComprobanteDetalleTable.c.item)
    return await execute_query(query, client_id=client_id)


async def get_comprobante_detalle_by_id(client_id: UUID, comprobante_detalle_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un detalle por id. Exige cliente_id para no cruzar tenants."""
    query = select(InvbillComprobanteDetalleTable).where(
        and_(
            InvbillComprobanteDetalleTable.c.cliente_id == client_id,
            InvbillComprobanteDetalleTable.c.comprobante_detalle_id == comprobante_detalle_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_comprobante_detalle(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un detalle. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("comprobante_detalle_id", uuid4())
    stmt = insert(InvbillComprobanteDetalleTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_comprobante_detalle_by_id(client_id, payload["comprobante_detalle_id"])


async def update_comprobante_detalle(
    client_id: UUID, comprobante_detalle_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un detalle. WHERE incluye cliente_id y comprobante_detalle_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("comprobante_detalle_id", "cliente_id")
    }
    if not payload:
        return await get_comprobante_detalle_by_id(client_id, comprobante_detalle_id)
    stmt = (
        update(InvbillComprobanteDetalleTable)
        .where(
            and_(
                InvbillComprobanteDetalleTable.c.cliente_id == client_id,
                InvbillComprobanteDetalleTable.c.comprobante_detalle_id == comprobante_detalle_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_comprobante_detalle_by_id(client_id, comprobante_detalle_id)
