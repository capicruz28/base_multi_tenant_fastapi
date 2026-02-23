"""
Queries SQLAlchemy Core para pur_cotizacion.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, date
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import PurCotizacionTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in PurCotizacionTable.c}


async def list_cotizaciones(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    proveedor_id: Optional[UUID] = None,
    solicitud_compra_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> List[Dict[str, Any]]:
    """Lista cotizaciones del tenant. Siempre filtra por cliente_id."""
    query = select(PurCotizacionTable).where(
        PurCotizacionTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(PurCotizacionTable.c.empresa_id == empresa_id)
    if proveedor_id:
        query = query.where(PurCotizacionTable.c.proveedor_id == proveedor_id)
    if solicitud_compra_id:
        query = query.where(PurCotizacionTable.c.solicitud_compra_id == solicitud_compra_id)
    if estado:
        query = query.where(PurCotizacionTable.c.estado == estado)
    if fecha_desde:
        query = query.where(PurCotizacionTable.c.fecha_cotizacion >= fecha_desde)
    if fecha_hasta:
        query = query.where(PurCotizacionTable.c.fecha_cotizacion <= fecha_hasta)
    query = query.order_by(PurCotizacionTable.c.fecha_cotizacion.desc())
    return await execute_query(query, client_id=client_id)


async def get_cotizacion_by_id(client_id: UUID, cotizacion_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una cotizacion por id. Exige cliente_id para no cruzar tenants."""
    query = select(PurCotizacionTable).where(
        and_(
            PurCotizacionTable.c.cliente_id == client_id,
            PurCotizacionTable.c.cotizacion_id == cotizacion_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_cotizacion(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una cotizacion. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("cotizacion_id", uuid4())
    stmt = insert(PurCotizacionTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_cotizacion_by_id(client_id, payload["cotizacion_id"])


async def update_cotizacion(
    client_id: UUID, cotizacion_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una cotizacion. WHERE incluye cliente_id y cotizacion_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("cotizacion_id", "cliente_id")
    }
    if not payload:
        return await get_cotizacion_by_id(client_id, cotizacion_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(PurCotizacionTable)
        .where(
            and_(
                PurCotizacionTable.c.cliente_id == client_id,
                PurCotizacionTable.c.cotizacion_id == cotizacion_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_cotizacion_by_id(client_id, cotizacion_id)
