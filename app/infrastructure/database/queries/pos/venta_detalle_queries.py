"""
Queries SQLAlchemy Core para pos_venta_detalle.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import PosVentaDetalleTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in PosVentaDetalleTable.c}


async def list_venta_detalles(
    client_id: UUID,
    venta_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    """Lista detalles de venta POS del tenant."""
    query = select(PosVentaDetalleTable).where(
        PosVentaDetalleTable.c.cliente_id == client_id
    )
    if venta_id:
        query = query.where(PosVentaDetalleTable.c.venta_id == venta_id)
    query = query.order_by(PosVentaDetalleTable.c.item)
    return await execute_query(query, client_id=client_id)


async def get_venta_detalle_by_id(
    client_id: UUID, venta_detalle_id: UUID
) -> Optional[Dict[str, Any]]:
    """Obtiene un detalle de venta por id."""
    query = select(PosVentaDetalleTable).where(
        and_(
            PosVentaDetalleTable.c.cliente_id == client_id,
            PosVentaDetalleTable.c.venta_detalle_id == venta_detalle_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_venta_detalle(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un detalle de venta."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("venta_detalle_id", uuid4())
    stmt = insert(PosVentaDetalleTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_venta_detalle_by_id(client_id, payload["venta_detalle_id"])


async def update_venta_detalle(
    client_id: UUID, venta_detalle_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un detalle de venta."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("venta_detalle_id", "cliente_id")
    }
    if not payload:
        return await get_venta_detalle_by_id(client_id, venta_detalle_id)
    stmt = (
        update(PosVentaDetalleTable)
        .where(
            and_(
                PosVentaDetalleTable.c.cliente_id == client_id,
                PosVentaDetalleTable.c.venta_detalle_id == venta_detalle_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_venta_detalle_by_id(client_id, venta_detalle_id)
