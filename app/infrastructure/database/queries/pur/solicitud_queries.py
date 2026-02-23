"""
Queries SQLAlchemy Core para pur_solicitud_compra.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, date
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import PurSolicitudCompraTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in PurSolicitudCompraTable.c}


async def list_solicitudes(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> List[Dict[str, Any]]:
    """Lista solicitudes del tenant. Siempre filtra por cliente_id."""
    query = select(PurSolicitudCompraTable).where(
        PurSolicitudCompraTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(PurSolicitudCompraTable.c.empresa_id == empresa_id)
    if estado:
        query = query.where(PurSolicitudCompraTable.c.estado == estado)
    if fecha_desde:
        query = query.where(PurSolicitudCompraTable.c.fecha_solicitud >= fecha_desde)
    if fecha_hasta:
        query = query.where(PurSolicitudCompraTable.c.fecha_solicitud <= fecha_hasta)
    query = query.order_by(PurSolicitudCompraTable.c.fecha_solicitud.desc())
    return await execute_query(query, client_id=client_id)


async def get_solicitud_by_id(client_id: UUID, solicitud_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una solicitud por id. Exige cliente_id para no cruzar tenants."""
    query = select(PurSolicitudCompraTable).where(
        and_(
            PurSolicitudCompraTable.c.cliente_id == client_id,
            PurSolicitudCompraTable.c.solicitud_id == solicitud_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_solicitud(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una solicitud. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("solicitud_id", uuid4())
    stmt = insert(PurSolicitudCompraTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_solicitud_by_id(client_id, payload["solicitud_id"])


async def update_solicitud(
    client_id: UUID, solicitud_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una solicitud. WHERE incluye cliente_id y solicitud_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("solicitud_id", "cliente_id")
    }
    if not payload:
        return await get_solicitud_by_id(client_id, solicitud_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(PurSolicitudCompraTable)
        .where(
            and_(
                PurSolicitudCompraTable.c.cliente_id == client_id,
                PurSolicitudCompraTable.c.solicitud_id == solicitud_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_solicitud_by_id(client_id, solicitud_id)
