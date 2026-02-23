"""Queries para mnt_orden_trabajo. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_
from app.infrastructure.database.tables_erp import MntOrdenTrabajoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in MntOrdenTrabajoTable.c}


async def list_orden_trabajo(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    activo_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    tipo_mantenimiento: Optional[str] = None,
    buscar: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = select(MntOrdenTrabajoTable).where(MntOrdenTrabajoTable.c.cliente_id == client_id)
    if empresa_id:
        q = q.where(MntOrdenTrabajoTable.c.empresa_id == empresa_id)
    if activo_id:
        q = q.where(MntOrdenTrabajoTable.c.activo_id == activo_id)
    if estado:
        q = q.where(MntOrdenTrabajoTable.c.estado == estado)
    if tipo_mantenimiento:
        q = q.where(MntOrdenTrabajoTable.c.tipo_mantenimiento == tipo_mantenimiento)
    if buscar:
        q = q.where(or_(
            MntOrdenTrabajoTable.c.numero_ot.ilike(f"%{buscar}%"),
            MntOrdenTrabajoTable.c.trabajo_a_realizar.ilike(f"%{buscar}%"),
        ))
    q = q.order_by(MntOrdenTrabajoTable.c.fecha_solicitud.desc())
    return await execute_query(q, client_id=client_id)


async def get_orden_trabajo_by_id(client_id: UUID, orden_trabajo_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(MntOrdenTrabajoTable).where(
        and_(
            MntOrdenTrabajoTable.c.cliente_id == client_id,
            MntOrdenTrabajoTable.c.orden_trabajo_id == orden_trabajo_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_orden_trabajo(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("orden_trabajo_id", uuid4())
    await execute_insert(insert(MntOrdenTrabajoTable).values(**payload), client_id=client_id)
    return await get_orden_trabajo_by_id(client_id, payload["orden_trabajo_id"])


async def update_orden_trabajo(
    client_id: UUID, orden_trabajo_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("orden_trabajo_id", "cliente_id")}
    if not payload:
        return await get_orden_trabajo_by_id(client_id, orden_trabajo_id)
    stmt = update(MntOrdenTrabajoTable).where(
        and_(
            MntOrdenTrabajoTable.c.cliente_id == client_id,
            MntOrdenTrabajoTable.c.orden_trabajo_id == orden_trabajo_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_orden_trabajo_by_id(client_id, orden_trabajo_id)
