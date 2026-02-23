"""Queries para mfg_orden_produccion_operacion. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_
from app.infrastructure.database.tables_erp import MfgOrdenProduccionOperacionTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in MfgOrdenProduccionOperacionTable.c}


async def list_orden_produccion_operaciones(
    client_id: UUID,
    orden_produccion_id: Optional[UUID] = None,
    centro_trabajo_id: Optional[UUID] = None,
    estado: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = select(MfgOrdenProduccionOperacionTable).where(
        MfgOrdenProduccionOperacionTable.c.cliente_id == client_id
    )
    if orden_produccion_id:
        q = q.where(MfgOrdenProduccionOperacionTable.c.orden_produccion_id == orden_produccion_id)
    if centro_trabajo_id:
        q = q.where(MfgOrdenProduccionOperacionTable.c.centro_trabajo_id == centro_trabajo_id)
    if estado:
        q = q.where(MfgOrdenProduccionOperacionTable.c.estado == estado)
    q = q.order_by(MfgOrdenProduccionOperacionTable.c.secuencia)
    return await execute_query(q, client_id=client_id)


async def get_orden_produccion_operacion_by_id(
    client_id: UUID, op_operacion_id: UUID
) -> Optional[Dict[str, Any]]:
    q = select(MfgOrdenProduccionOperacionTable).where(
        and_(
            MfgOrdenProduccionOperacionTable.c.cliente_id == client_id,
            MfgOrdenProduccionOperacionTable.c.op_operacion_id == op_operacion_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_orden_produccion_operacion(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("op_operacion_id", uuid4())
    await execute_insert(insert(MfgOrdenProduccionOperacionTable).values(**payload), client_id=client_id)
    return await get_orden_produccion_operacion_by_id(client_id, payload["op_operacion_id"])


async def update_orden_produccion_operacion(
    client_id: UUID, op_operacion_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("op_operacion_id", "cliente_id")}
    if not payload:
        return await get_orden_produccion_operacion_by_id(client_id, op_operacion_id)
    stmt = update(MfgOrdenProduccionOperacionTable).where(
        and_(
            MfgOrdenProduccionOperacionTable.c.cliente_id == client_id,
            MfgOrdenProduccionOperacionTable.c.op_operacion_id == op_operacion_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_orden_produccion_operacion_by_id(client_id, op_operacion_id)
