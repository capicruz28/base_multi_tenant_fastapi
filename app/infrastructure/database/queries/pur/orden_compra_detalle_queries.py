"""
Queries SQLAlchemy Core para pur_orden_compra_detalle.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import PurOrdenCompraDetalleTable
from app.infrastructure.database.queries_async import (
    execute_query,
    execute_insert,
    execute_update,
)

_COLUMNS = {c.name for c in PurOrdenCompraDetalleTable.c}
_COMPUTED = frozenset(
    {"precio_neto", "subtotal", "igv", "total", "cantidad_pendiente"}
)
_WRITABLE_COLUMNS = _COLUMNS - _COMPUTED


async def list_ordenes_compra_detalle(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    orden_compra_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    """Lista líneas de orden de compra del tenant. Siempre filtra por cliente_id."""
    query = select(PurOrdenCompraDetalleTable).where(
        PurOrdenCompraDetalleTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(PurOrdenCompraDetalleTable.c.empresa_id == empresa_id)
    if orden_compra_id:
        query = query.where(
            PurOrdenCompraDetalleTable.c.orden_compra_id == orden_compra_id
        )
    if producto_id:
        query = query.where(PurOrdenCompraDetalleTable.c.producto_id == producto_id)
    query = query.order_by(
        PurOrdenCompraDetalleTable.c.orden_compra_id,
        PurOrdenCompraDetalleTable.c.producto_id,
    )
    return await execute_query(query, client_id=client_id)


async def get_orden_compra_detalle_by_id(
    client_id: UUID, orden_compra_detalle_id: UUID
) -> Optional[Dict[str, Any]]:
    """Obtiene una línea de orden de compra por id. Exige cliente_id para no cruzar tenants."""
    query = select(PurOrdenCompraDetalleTable).where(
        and_(
            PurOrdenCompraDetalleTable.c.cliente_id == client_id,
            PurOrdenCompraDetalleTable.c.orden_compra_detalle_id
            == orden_compra_detalle_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_orden_compra_detalle(
    client_id: UUID, data: Dict[str, Any]
) -> Dict[str, Any]:
    """Inserta una línea de orden de compra. cliente_id se fuerza desde contexto."""
    from uuid import uuid4

    payload = {k: v for k, v in data.items() if k in _WRITABLE_COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("orden_compra_detalle_id", uuid4())
    stmt = insert(PurOrdenCompraDetalleTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_orden_compra_detalle_by_id(
        client_id, payload["orden_compra_detalle_id"]
    )


async def update_orden_compra_detalle(
    client_id: UUID, orden_compra_detalle_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una línea de orden de compra. WHERE incluye cliente_id e id de detalle."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _WRITABLE_COLUMNS
        and k
        not in (
            "orden_compra_detalle_id",
            "cliente_id",
        )
    }
    if not payload:
        return await get_orden_compra_detalle_by_id(
            client_id, orden_compra_detalle_id
        )
    stmt = (
        update(PurOrdenCompraDetalleTable)
        .where(
            and_(
                PurOrdenCompraDetalleTable.c.cliente_id == client_id,
                PurOrdenCompraDetalleTable.c.orden_compra_detalle_id
                == orden_compra_detalle_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_orden_compra_detalle_by_id(
        client_id, orden_compra_detalle_id
    )
