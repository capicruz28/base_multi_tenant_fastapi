"""Queries para bdg_presupuesto. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_
from app.infrastructure.database.tables_erp import BdgPresupuestoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in BdgPresupuestoTable.c}


async def list_presupuesto(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    anio: Optional[int] = None,
    tipo_presupuesto: Optional[str] = None,
    estado: Optional[str] = None,
    buscar: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = select(BdgPresupuestoTable).where(BdgPresupuestoTable.c.cliente_id == client_id)
    if empresa_id:
        q = q.where(BdgPresupuestoTable.c.empresa_id == empresa_id)
    if anio is not None:
        q = q.where(BdgPresupuestoTable.c["año"] == anio)
    if tipo_presupuesto:
        q = q.where(BdgPresupuestoTable.c.tipo_presupuesto == tipo_presupuesto)
    if estado:
        q = q.where(BdgPresupuestoTable.c.estado == estado)
    if buscar:
        q = q.where(or_(
            BdgPresupuestoTable.c.nombre.ilike(f"%{buscar}%"),
            BdgPresupuestoTable.c.codigo_presupuesto.ilike(f"%{buscar}%"),
        ))
    q = q.order_by(BdgPresupuestoTable.c["año"].desc(), BdgPresupuestoTable.c.codigo_presupuesto)
    return await execute_query(q, client_id=client_id)


async def get_presupuesto_by_id(client_id: UUID, presupuesto_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(BdgPresupuestoTable).where(
        and_(
            BdgPresupuestoTable.c.cliente_id == client_id,
            BdgPresupuestoTable.c.presupuesto_id == presupuesto_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_presupuesto(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("presupuesto_id", uuid4())
    await execute_insert(insert(BdgPresupuestoTable).values(**payload), client_id=client_id)
    return await get_presupuesto_by_id(client_id, payload["presupuesto_id"])


async def update_presupuesto(
    client_id: UUID, presupuesto_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("presupuesto_id", "cliente_id")}
    if not payload:
        return await get_presupuesto_by_id(client_id, presupuesto_id)
    stmt = update(BdgPresupuestoTable).where(
        and_(
            BdgPresupuestoTable.c.cliente_id == client_id,
            BdgPresupuestoTable.c.presupuesto_id == presupuesto_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_presupuesto_by_id(client_id, presupuesto_id)
