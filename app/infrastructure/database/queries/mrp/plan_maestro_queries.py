"""Queries para mrp_plan_maestro. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_
from app.infrastructure.database.tables_erp import MrpPlanMaestroTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in MrpPlanMaestroTable.c}


async def list_plan_maestro(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    buscar: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = select(MrpPlanMaestroTable).where(MrpPlanMaestroTable.c.cliente_id == client_id)
    if empresa_id:
        q = q.where(MrpPlanMaestroTable.c.empresa_id == empresa_id)
    if estado:
        q = q.where(MrpPlanMaestroTable.c.estado == estado)
    if buscar:
        q = q.where(or_(
            MrpPlanMaestroTable.c.nombre.ilike(f"%{buscar}%"),
            MrpPlanMaestroTable.c.codigo_plan.ilike(f"%{buscar}%"),
        ))
    q = q.order_by(MrpPlanMaestroTable.c.fecha_inicio.desc())
    return await execute_query(q, client_id=client_id)


async def get_plan_maestro_by_id(client_id: UUID, plan_maestro_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(MrpPlanMaestroTable).where(
        and_(
            MrpPlanMaestroTable.c.cliente_id == client_id,
            MrpPlanMaestroTable.c.plan_maestro_id == plan_maestro_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_plan_maestro(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("plan_maestro_id", uuid4())
    await execute_insert(insert(MrpPlanMaestroTable).values(**payload), client_id=client_id)
    return await get_plan_maestro_by_id(client_id, payload["plan_maestro_id"])


async def update_plan_maestro(
    client_id: UUID, plan_maestro_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("plan_maestro_id", "cliente_id")}
    if not payload:
        return await get_plan_maestro_by_id(client_id, plan_maestro_id)
    stmt = update(MrpPlanMaestroTable).where(
        and_(
            MrpPlanMaestroTable.c.cliente_id == client_id,
            MrpPlanMaestroTable.c.plan_maestro_id == plan_maestro_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_plan_maestro_by_id(client_id, plan_maestro_id)
