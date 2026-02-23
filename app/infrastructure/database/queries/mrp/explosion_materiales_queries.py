"""Queries para mrp_explosion_materiales. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_
from app.infrastructure.database.tables_erp import MrpExplosionMaterialesTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in MrpExplosionMaterialesTable.c}


async def list_explosion_materiales(
    client_id: UUID,
    plan_maestro_id: Optional[UUID] = None,
    producto_componente_id: Optional[UUID] = None,
    nivel_bom: Optional[int] = None,
) -> List[Dict[str, Any]]:
    q = select(MrpExplosionMaterialesTable).where(MrpExplosionMaterialesTable.c.cliente_id == client_id)
    if plan_maestro_id:
        q = q.where(MrpExplosionMaterialesTable.c.plan_maestro_id == plan_maestro_id)
    if producto_componente_id:
        q = q.where(MrpExplosionMaterialesTable.c.producto_componente_id == producto_componente_id)
    if nivel_bom is not None:
        q = q.where(MrpExplosionMaterialesTable.c.nivel_bom == nivel_bom)
    q = q.order_by(MrpExplosionMaterialesTable.c.nivel_bom, MrpExplosionMaterialesTable.c.fecha_requerida)
    return await execute_query(q, client_id=client_id)


async def get_explosion_materiales_by_id(client_id: UUID, explosion_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(MrpExplosionMaterialesTable).where(
        and_(
            MrpExplosionMaterialesTable.c.cliente_id == client_id,
            MrpExplosionMaterialesTable.c.explosion_id == explosion_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_explosion_materiales(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("explosion_id", uuid4())
    await execute_insert(insert(MrpExplosionMaterialesTable).values(**payload), client_id=client_id)
    return await get_explosion_materiales_by_id(client_id, payload["explosion_id"])


async def update_explosion_materiales(
    client_id: UUID, explosion_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("explosion_id", "cliente_id")}
    if not payload:
        return await get_explosion_materiales_by_id(client_id, explosion_id)
    stmt = update(MrpExplosionMaterialesTable).where(
        and_(
            MrpExplosionMaterialesTable.c.cliente_id == client_id,
            MrpExplosionMaterialesTable.c.explosion_id == explosion_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_explosion_materiales_by_id(client_id, explosion_id)
