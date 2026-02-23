"""Queries para mrp_necesidad_bruta. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_
from app.infrastructure.database.tables_erp import MrpNecesidadBrutaTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in MrpNecesidadBrutaTable.c}


async def list_necesidad_bruta(
    client_id: UUID,
    plan_maestro_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    origen: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = select(MrpNecesidadBrutaTable).where(MrpNecesidadBrutaTable.c.cliente_id == client_id)
    if plan_maestro_id:
        q = q.where(MrpNecesidadBrutaTable.c.plan_maestro_id == plan_maestro_id)
    if producto_id:
        q = q.where(MrpNecesidadBrutaTable.c.producto_id == producto_id)
    if origen:
        q = q.where(MrpNecesidadBrutaTable.c.origen == origen)
    q = q.order_by(MrpNecesidadBrutaTable.c.fecha_requerida, MrpNecesidadBrutaTable.c.producto_id)
    return await execute_query(q, client_id=client_id)


async def get_necesidad_bruta_by_id(client_id: UUID, necesidad_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(MrpNecesidadBrutaTable).where(
        and_(
            MrpNecesidadBrutaTable.c.cliente_id == client_id,
            MrpNecesidadBrutaTable.c.necesidad_id == necesidad_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_necesidad_bruta(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("necesidad_id", uuid4())
    await execute_insert(insert(MrpNecesidadBrutaTable).values(**payload), client_id=client_id)
    return await get_necesidad_bruta_by_id(client_id, payload["necesidad_id"])


async def update_necesidad_bruta(
    client_id: UUID, necesidad_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("necesidad_id", "cliente_id")}
    if not payload:
        return await get_necesidad_bruta_by_id(client_id, necesidad_id)
    stmt = update(MrpNecesidadBrutaTable).where(
        and_(
            MrpNecesidadBrutaTable.c.cliente_id == client_id,
            MrpNecesidadBrutaTable.c.necesidad_id == necesidad_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_necesidad_bruta_by_id(client_id, necesidad_id)
