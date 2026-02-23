"""Queries para mnt_plan_mantenimiento. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_
from app.infrastructure.database.tables_erp import MntPlanMantenimientoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in MntPlanMantenimientoTable.c}


async def list_plan_mantenimiento(
    client_id: UUID,
    activo_id: Optional[UUID] = None,
    tipo_mantenimiento: Optional[str] = None,
    es_activo: Optional[bool] = None,
    buscar: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = select(MntPlanMantenimientoTable).where(MntPlanMantenimientoTable.c.cliente_id == client_id)
    if activo_id:
        q = q.where(MntPlanMantenimientoTable.c.activo_id == activo_id)
    if tipo_mantenimiento:
        q = q.where(MntPlanMantenimientoTable.c.tipo_mantenimiento == tipo_mantenimiento)
    if es_activo is not None:
        q = q.where(MntPlanMantenimientoTable.c.es_activo == es_activo)
    if buscar:
        q = q.where(or_(
            MntPlanMantenimientoTable.c.nombre.ilike(f"%{buscar}%"),
            MntPlanMantenimientoTable.c.codigo_plan.ilike(f"%{buscar}%"),
        ))
    q = q.order_by(MntPlanMantenimientoTable.c.fecha_proximo_mantenimiento, MntPlanMantenimientoTable.c.codigo_plan)
    return await execute_query(q, client_id=client_id)


async def get_plan_mantenimiento_by_id(client_id: UUID, plan_mantenimiento_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(MntPlanMantenimientoTable).where(
        and_(
            MntPlanMantenimientoTable.c.cliente_id == client_id,
            MntPlanMantenimientoTable.c.plan_mantenimiento_id == plan_mantenimiento_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_plan_mantenimiento(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("plan_mantenimiento_id", uuid4())
    await execute_insert(insert(MntPlanMantenimientoTable).values(**payload), client_id=client_id)
    return await get_plan_mantenimiento_by_id(client_id, payload["plan_mantenimiento_id"])


async def update_plan_mantenimiento(
    client_id: UUID, plan_mantenimiento_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("plan_mantenimiento_id", "cliente_id")}
    if not payload:
        return await get_plan_mantenimiento_by_id(client_id, plan_mantenimiento_id)
    stmt = update(MntPlanMantenimientoTable).where(
        and_(
            MntPlanMantenimientoTable.c.cliente_id == client_id,
            MntPlanMantenimientoTable.c.plan_mantenimiento_id == plan_mantenimiento_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_plan_mantenimiento_by_id(client_id, plan_mantenimiento_id)
