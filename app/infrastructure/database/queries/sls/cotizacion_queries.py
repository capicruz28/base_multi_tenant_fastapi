"""
Queries SQLAlchemy Core para sls_cotizacion.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, date
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import SlsCotizacionTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in SlsCotizacionTable.c}


async def list_cotizaciones(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    cliente_venta_id: Optional[UUID] = None,
    vendedor_usuario_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> List[Dict[str, Any]]:
    """Lista cotizaciones del tenant. Siempre filtra por cliente_id."""
    query = select(SlsCotizacionTable).where(
        SlsCotizacionTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(SlsCotizacionTable.c.empresa_id == empresa_id)
    if cliente_venta_id:
        query = query.where(SlsCotizacionTable.c.cliente_venta_id == cliente_venta_id)
    if vendedor_usuario_id:
        query = query.where(SlsCotizacionTable.c.vendedor_usuario_id == vendedor_usuario_id)
    if estado:
        query = query.where(SlsCotizacionTable.c.estado == estado)
    if fecha_desde:
        query = query.where(SlsCotizacionTable.c.fecha_cotizacion >= fecha_desde)
    if fecha_hasta:
        query = query.where(SlsCotizacionTable.c.fecha_cotizacion <= fecha_hasta)
    query = query.order_by(SlsCotizacionTable.c.fecha_cotizacion.desc())
    return await execute_query(query, client_id=client_id)


async def get_cotizacion_by_id(client_id: UUID, cotizacion_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una cotizacion por id. Exige cliente_id para no cruzar tenants."""
    query = select(SlsCotizacionTable).where(
        and_(
            SlsCotizacionTable.c.cliente_id == client_id,
            SlsCotizacionTable.c.cotizacion_id == cotizacion_id,
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
    stmt = insert(SlsCotizacionTable).values(**payload)
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
        update(SlsCotizacionTable)
        .where(
            and_(
                SlsCotizacionTable.c.cliente_id == client_id,
                SlsCotizacionTable.c.cotizacion_id == cotizacion_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_cotizacion_by_id(client_id, cotizacion_id)
