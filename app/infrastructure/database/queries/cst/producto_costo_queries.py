"""Queries para cst_producto_costo. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_
from app.infrastructure.database.tables_erp import CstProductoCostoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in CstProductoCostoTable.c}


async def list_producto_costo(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    anio: Optional[int] = None,
    mes: Optional[int] = None,
    metodo_costeo: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = select(CstProductoCostoTable).where(CstProductoCostoTable.c.cliente_id == client_id)
    if empresa_id:
        q = q.where(CstProductoCostoTable.c.empresa_id == empresa_id)
    if producto_id:
        q = q.where(CstProductoCostoTable.c.producto_id == producto_id)
    if anio is not None:
        q = q.where(CstProductoCostoTable.c["año"] == anio)
    if mes is not None:
        q = q.where(CstProductoCostoTable.c.mes == mes)
    if metodo_costeo:
        q = q.where(CstProductoCostoTable.c.metodo_costeo == metodo_costeo)
    q = q.order_by(CstProductoCostoTable.c["año"].desc(), CstProductoCostoTable.c.mes.desc(), CstProductoCostoTable.c.producto_id)
    return await execute_query(q, client_id=client_id)


async def get_producto_costo_by_id(client_id: UUID, producto_costo_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(CstProductoCostoTable).where(
        and_(
            CstProductoCostoTable.c.cliente_id == client_id,
            CstProductoCostoTable.c.producto_costo_id == producto_costo_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_producto_costo(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("producto_costo_id", uuid4())
    await execute_insert(insert(CstProductoCostoTable).values(**payload), client_id=client_id)
    return await get_producto_costo_by_id(client_id, payload["producto_costo_id"])


async def update_producto_costo(
    client_id: UUID, producto_costo_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("producto_costo_id", "cliente_id")}
    if not payload:
        return await get_producto_costo_by_id(client_id, producto_costo_id)
    stmt = update(CstProductoCostoTable).where(
        and_(
            CstProductoCostoTable.c.cliente_id == client_id,
            CstProductoCostoTable.c.producto_costo_id == producto_costo_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_producto_costo_by_id(client_id, producto_costo_id)
