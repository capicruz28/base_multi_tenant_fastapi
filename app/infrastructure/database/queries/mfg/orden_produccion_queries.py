"""Queries para mfg_orden_produccion. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import date
from sqlalchemy import select, insert, update, and_
from app.infrastructure.database.tables_erp import MfgOrdenProduccionTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in MfgOrdenProduccionTable.c}


async def list_ordenes_produccion(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> List[Dict[str, Any]]:
    q = select(MfgOrdenProduccionTable).where(MfgOrdenProduccionTable.c.cliente_id == client_id)
    if empresa_id:
        q = q.where(MfgOrdenProduccionTable.c.empresa_id == empresa_id)
    if producto_id:
        q = q.where(MfgOrdenProduccionTable.c.producto_id == producto_id)
    if estado:
        q = q.where(MfgOrdenProduccionTable.c.estado == estado)
    if fecha_desde:
        q = q.where(MfgOrdenProduccionTable.c.fecha_inicio_programada >= fecha_desde)
    if fecha_hasta:
        q = q.where(MfgOrdenProduccionTable.c.fecha_inicio_programada <= fecha_hasta)
    q = q.order_by(MfgOrdenProduccionTable.c.fecha_emision.desc())
    return await execute_query(q, client_id=client_id)


async def get_orden_produccion_by_id(
    client_id: UUID, orden_produccion_id: UUID
) -> Optional[Dict[str, Any]]:
    q = select(MfgOrdenProduccionTable).where(
        and_(
            MfgOrdenProduccionTable.c.cliente_id == client_id,
            MfgOrdenProduccionTable.c.orden_produccion_id == orden_produccion_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_orden_produccion(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("orden_produccion_id", uuid4())
    await execute_insert(insert(MfgOrdenProduccionTable).values(**payload), client_id=client_id)
    return await get_orden_produccion_by_id(client_id, payload["orden_produccion_id"])


async def update_orden_produccion(
    client_id: UUID, orden_produccion_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("orden_produccion_id", "cliente_id")}
    if not payload:
        return await get_orden_produccion_by_id(client_id, orden_produccion_id)
    stmt = update(MfgOrdenProduccionTable).where(
        and_(
            MfgOrdenProduccionTable.c.cliente_id == client_id,
            MfgOrdenProduccionTable.c.orden_produccion_id == orden_produccion_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_orden_produccion_by_id(client_id, orden_produccion_id)
