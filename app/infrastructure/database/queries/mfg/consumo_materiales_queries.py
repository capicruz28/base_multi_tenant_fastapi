"""Queries para mfg_consumo_materiales. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_
from app.infrastructure.database.tables_erp import MfgConsumoMaterialesTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in MfgConsumoMaterialesTable.c}


async def list_consumo_materiales(
    client_id: UUID,
    orden_produccion_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    q = select(MfgConsumoMaterialesTable).where(MfgConsumoMaterialesTable.c.cliente_id == client_id)
    if orden_produccion_id:
        q = q.where(MfgConsumoMaterialesTable.c.orden_produccion_id == orden_produccion_id)
    if producto_id:
        q = q.where(MfgConsumoMaterialesTable.c.producto_id == producto_id)
    q = q.order_by(MfgConsumoMaterialesTable.c.fecha_consumo.desc())
    return await execute_query(q, client_id=client_id)


async def get_consumo_materiales_by_id(
    client_id: UUID, consumo_id: UUID
) -> Optional[Dict[str, Any]]:
    q = select(MfgConsumoMaterialesTable).where(
        and_(
            MfgConsumoMaterialesTable.c.cliente_id == client_id,
            MfgConsumoMaterialesTable.c.consumo_id == consumo_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_consumo_materiales(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("consumo_id", uuid4())
    await execute_insert(insert(MfgConsumoMaterialesTable).values(**payload), client_id=client_id)
    return await get_consumo_materiales_by_id(client_id, payload["consumo_id"])


async def update_consumo_materiales(
    client_id: UUID, consumo_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("consumo_id", "cliente_id")}
    if not payload:
        return await get_consumo_materiales_by_id(client_id, consumo_id)
    stmt = update(MfgConsumoMaterialesTable).where(
        and_(
            MfgConsumoMaterialesTable.c.cliente_id == client_id,
            MfgConsumoMaterialesTable.c.consumo_id == consumo_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_consumo_materiales_by_id(client_id, consumo_id)
