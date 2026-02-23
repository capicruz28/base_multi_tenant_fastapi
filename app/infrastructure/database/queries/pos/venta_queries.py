"""
Queries SQLAlchemy Core para pos_venta.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import PosVentaTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in PosVentaTable.c}


async def list_ventas(
    client_id: UUID,
    punto_venta_id: Optional[UUID] = None,
    turno_caja_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Lista ventas POS del tenant."""
    query = select(PosVentaTable).where(
        PosVentaTable.c.cliente_id == client_id
    )
    if punto_venta_id:
        query = query.where(PosVentaTable.c.punto_venta_id == punto_venta_id)
    if turno_caja_id:
        query = query.where(PosVentaTable.c.turno_caja_id == turno_caja_id)
    if estado:
        query = query.where(PosVentaTable.c.estado == estado)
    if fecha_desde:
        query = query.where(PosVentaTable.c.fecha_venta >= fecha_desde)
    if fecha_hasta:
        query = query.where(PosVentaTable.c.fecha_venta <= fecha_hasta)
    query = query.order_by(PosVentaTable.c.fecha_venta.desc())
    return await execute_query(query, client_id=client_id)


async def get_venta_by_id(client_id: UUID, venta_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una venta POS por id."""
    query = select(PosVentaTable).where(
        and_(
            PosVentaTable.c.cliente_id == client_id,
            PosVentaTable.c.venta_id == venta_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_venta(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una venta POS."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("venta_id", uuid4())
    stmt = insert(PosVentaTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_venta_by_id(client_id, payload["venta_id"])


async def update_venta(
    client_id: UUID, venta_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una venta POS (ej. anulación)."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("venta_id", "cliente_id")
    }
    if not payload:
        return await get_venta_by_id(client_id, venta_id)
    stmt = (
        update(PosVentaTable)
        .where(
            and_(
                PosVentaTable.c.cliente_id == client_id,
                PosVentaTable.c.venta_id == venta_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_venta_by_id(client_id, venta_id)
