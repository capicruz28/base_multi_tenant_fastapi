"""Queries para mrp_orden_sugerida. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_
from app.infrastructure.database.tables_erp import MrpOrdenSugeridaTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in MrpOrdenSugeridaTable.c}


async def list_orden_sugerida(
    client_id: UUID,
    plan_maestro_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    tipo_orden: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = select(MrpOrdenSugeridaTable).where(MrpOrdenSugeridaTable.c.cliente_id == client_id)
    if plan_maestro_id:
        q = q.where(MrpOrdenSugeridaTable.c.plan_maestro_id == plan_maestro_id)
    if producto_id:
        q = q.where(MrpOrdenSugeridaTable.c.producto_id == producto_id)
    if estado:
        q = q.where(MrpOrdenSugeridaTable.c.estado == estado)
    if tipo_orden:
        q = q.where(MrpOrdenSugeridaTable.c.tipo_orden == tipo_orden)
    q = q.order_by(MrpOrdenSugeridaTable.c.fecha_requerida, MrpOrdenSugeridaTable.c.producto_id)
    return await execute_query(q, client_id=client_id)


async def get_orden_sugerida_by_id(client_id: UUID, orden_sugerida_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(MrpOrdenSugeridaTable).where(
        and_(
            MrpOrdenSugeridaTable.c.cliente_id == client_id,
            MrpOrdenSugeridaTable.c.orden_sugerida_id == orden_sugerida_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_orden_sugerida(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("orden_sugerida_id", uuid4())
    await execute_insert(insert(MrpOrdenSugeridaTable).values(**payload), client_id=client_id)
    return await get_orden_sugerida_by_id(client_id, payload["orden_sugerida_id"])


async def update_orden_sugerida(
    client_id: UUID, orden_sugerida_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("orden_sugerida_id", "cliente_id")}
    if not payload:
        return await get_orden_sugerida_by_id(client_id, orden_sugerida_id)
    stmt = update(MrpOrdenSugeridaTable).where(
        and_(
            MrpOrdenSugeridaTable.c.cliente_id == client_id,
            MrpOrdenSugeridaTable.c.orden_sugerida_id == orden_sugerida_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_orden_sugerida_by_id(client_id, orden_sugerida_id)
