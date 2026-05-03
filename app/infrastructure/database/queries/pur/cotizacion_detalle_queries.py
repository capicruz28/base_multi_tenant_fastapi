"""
Queries SQLAlchemy Core para pur_cotizacion_detalle.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import PurCotizacionDetalleTable
from app.infrastructure.database.queries_async import (
    execute_query,
    execute_insert,
    execute_update,
)

_COLUMNS = {c.name for c in PurCotizacionDetalleTable.c}


async def list_cotizaciones_detalle(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    cotizacion_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    """Lista líneas de cotizaciones del tenant. Siempre filtra por cliente_id."""
    query = select(PurCotizacionDetalleTable).where(
        PurCotizacionDetalleTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(PurCotizacionDetalleTable.c.empresa_id == empresa_id)
    if cotizacion_id:
        query = query.where(PurCotizacionDetalleTable.c.cotizacion_id == cotizacion_id)
    if producto_id:
        query = query.where(PurCotizacionDetalleTable.c.producto_id == producto_id)
    query = query.order_by(
        PurCotizacionDetalleTable.c.cotizacion_id,
        PurCotizacionDetalleTable.c.producto_id,
    )
    return await execute_query(query, client_id=client_id)


async def get_cotizacion_detalle_by_id(
    client_id: UUID, cotizacion_detalle_id: UUID
) -> Optional[Dict[str, Any]]:
    """Obtiene una línea de cotización por id. Exige cliente_id para no cruzar tenants."""
    query = select(PurCotizacionDetalleTable).where(
        and_(
            PurCotizacionDetalleTable.c.cliente_id == client_id,
            PurCotizacionDetalleTable.c.cotizacion_detalle_id == cotizacion_detalle_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_cotizacion_detalle(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una línea de cotización. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4

    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("cotizacion_detalle_id", uuid4())
    stmt = insert(PurCotizacionDetalleTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_cotizacion_detalle_by_id(client_id, payload["cotizacion_detalle_id"])


async def update_cotizacion_detalle(
    client_id: UUID, cotizacion_detalle_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una línea de cotización. WHERE incluye cliente_id e id de detalle."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _COLUMNS
        and k
        not in (
            "cotizacion_detalle_id",
            "cliente_id",
        )
    }
    if not payload:
        return await get_cotizacion_detalle_by_id(client_id, cotizacion_detalle_id)
    stmt = (
        update(PurCotizacionDetalleTable)
        .where(
            and_(
                PurCotizacionDetalleTable.c.cliente_id == client_id,
                PurCotizacionDetalleTable.c.cotizacion_detalle_id
                == cotizacion_detalle_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_cotizacion_detalle_by_id(client_id, cotizacion_detalle_id)


