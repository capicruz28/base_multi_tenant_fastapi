"""Queries para mnt_historial_mantenimiento. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_
from app.infrastructure.database.tables_erp import MntHistorialMantenimientoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in MntHistorialMantenimientoTable.c}


async def list_historial_mantenimiento(
    client_id: UUID,
    activo_id: Optional[UUID] = None,
    orden_trabajo_id: Optional[UUID] = None,
    tipo_mantenimiento: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = select(MntHistorialMantenimientoTable).where(MntHistorialMantenimientoTable.c.cliente_id == client_id)
    if activo_id:
        q = q.where(MntHistorialMantenimientoTable.c.activo_id == activo_id)
    if orden_trabajo_id:
        q = q.where(MntHistorialMantenimientoTable.c.orden_trabajo_id == orden_trabajo_id)
    if tipo_mantenimiento:
        q = q.where(MntHistorialMantenimientoTable.c.tipo_mantenimiento == tipo_mantenimiento)
    q = q.order_by(MntHistorialMantenimientoTable.c.fecha_mantenimiento.desc())
    return await execute_query(q, client_id=client_id)


async def get_historial_mantenimiento_by_id(client_id: UUID, historial_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(MntHistorialMantenimientoTable).where(
        and_(
            MntHistorialMantenimientoTable.c.cliente_id == client_id,
            MntHistorialMantenimientoTable.c.historial_id == historial_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_historial_mantenimiento(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("historial_id", uuid4())
    await execute_insert(insert(MntHistorialMantenimientoTable).values(**payload), client_id=client_id)
    return await get_historial_mantenimiento_by_id(client_id, payload["historial_id"])


async def update_historial_mantenimiento(
    client_id: UUID, historial_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("historial_id", "cliente_id")}
    if not payload:
        return await get_historial_mantenimiento_by_id(client_id, historial_id)
    stmt = update(MntHistorialMantenimientoTable).where(
        and_(
            MntHistorialMantenimientoTable.c.cliente_id == client_id,
            MntHistorialMantenimientoTable.c.historial_id == historial_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_historial_mantenimiento_by_id(client_id, historial_id)
