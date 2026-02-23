"""Queries para mps_plan_produccion_detalle. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_
from app.infrastructure.database.tables_erp import MpsPlanProduccionDetalleTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in MpsPlanProduccionDetalleTable.c}


async def list_plan_produccion_detalle(
    client_id: UUID,
    plan_produccion_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    q = select(MpsPlanProduccionDetalleTable).where(MpsPlanProduccionDetalleTable.c.cliente_id == client_id)
    if plan_produccion_id:
        q = q.where(MpsPlanProduccionDetalleTable.c.plan_produccion_id == plan_produccion_id)
    if producto_id:
        q = q.where(MpsPlanProduccionDetalleTable.c.producto_id == producto_id)
    q = q.order_by(MpsPlanProduccionDetalleTable.c.fecha_inicio, MpsPlanProduccionDetalleTable.c.producto_id)
    return await execute_query(q, client_id=client_id)


async def get_plan_produccion_detalle_by_id(client_id: UUID, plan_detalle_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(MpsPlanProduccionDetalleTable).where(
        and_(
            MpsPlanProduccionDetalleTable.c.cliente_id == client_id,
            MpsPlanProduccionDetalleTable.c.plan_detalle_id == plan_detalle_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_plan_produccion_detalle(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("plan_detalle_id", uuid4())
    await execute_insert(insert(MpsPlanProduccionDetalleTable).values(**payload), client_id=client_id)
    return await get_plan_produccion_detalle_by_id(client_id, payload["plan_detalle_id"])


async def update_plan_produccion_detalle(
    client_id: UUID, plan_detalle_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("plan_detalle_id", "cliente_id")}
    if not payload:
        return await get_plan_produccion_detalle_by_id(client_id, plan_detalle_id)
    stmt = update(MpsPlanProduccionDetalleTable).where(
        and_(
            MpsPlanProduccionDetalleTable.c.cliente_id == client_id,
            MpsPlanProduccionDetalleTable.c.plan_detalle_id == plan_detalle_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_plan_produccion_detalle_by_id(client_id, plan_detalle_id)
