"""
Queries SQLAlchemy Core para pos_venta_detalle.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import PosVentaTable, PosVentaDetalleTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in PosVentaDetalleTable.c}
_SKIP_ON_WRITE = frozenset(
    {
        "venta_detalle_id",
        "cliente_id",
        "descuento_monto",
        "precio_neto",
        "subtotal",
        "igv",
        "total",
    }
)


async def list_venta_detalles(
    client_id: UUID,
    venta_id: Optional[UUID] = None,
    empresa_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    """Lista detalles de venta POS del tenant."""
    query = select(PosVentaDetalleTable).where(
        PosVentaDetalleTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(PosVentaDetalleTable.c.empresa_id == empresa_id)
    if venta_id:
        query = query.where(PosVentaDetalleTable.c.venta_id == venta_id)
    query = query.order_by(PosVentaDetalleTable.c.item)
    return await execute_query(query, client_id=client_id)


async def get_venta_detalle_by_id(
    client_id: UUID,
    venta_detalle_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Obtiene un detalle de venta por id. Si empresa_id se informa, debe coincidir."""
    cond = [
        PosVentaDetalleTable.c.cliente_id == client_id,
        PosVentaDetalleTable.c.venta_detalle_id == venta_detalle_id,
    ]
    if empresa_id is not None:
        cond.append(PosVentaDetalleTable.c.empresa_id == empresa_id)
    query = select(PosVentaDetalleTable).where(and_(*cond))
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_venta_detalle(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un detalle de venta."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in _SKIP_ON_WRITE}
    payload["cliente_id"] = client_id
    payload.setdefault("venta_detalle_id", uuid4())
    # Fase 5: empresa_id es obligatorio; derivarlo desde la venta (cabecera)
    venta_id = payload.get("venta_id")
    if venta_id:
        q = select(PosVentaTable.c.empresa_id).where(
            and_(
                PosVentaTable.c.cliente_id == client_id,
                PosVentaTable.c.venta_id == venta_id,
            )
        )
        rows = await execute_query(q, client_id=client_id)
        if rows:
            payload["empresa_id"] = rows[0]["empresa_id"]
    stmt = insert(PosVentaDetalleTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_venta_detalle_by_id(client_id, payload["venta_detalle_id"])


async def update_venta_detalle(
    client_id: UUID,
    venta_detalle_id: UUID,
    data: Dict[str, Any],
    empresa_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Actualiza un detalle de venta."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _COLUMNS and k not in _SKIP_ON_WRITE
    }
    if not payload:
        return await get_venta_detalle_by_id(
            client_id, venta_detalle_id, empresa_id=empresa_id
        )
    cond = [
        PosVentaDetalleTable.c.cliente_id == client_id,
        PosVentaDetalleTable.c.venta_detalle_id == venta_detalle_id,
    ]
    if empresa_id is not None:
        cond.append(PosVentaDetalleTable.c.empresa_id == empresa_id)
    stmt = update(PosVentaDetalleTable).where(and_(*cond)).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_venta_detalle_by_id(
        client_id, venta_detalle_id, empresa_id=empresa_id
    )
