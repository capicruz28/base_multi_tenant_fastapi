"""Queries para bdg_presupuesto_detalle. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_
from app.infrastructure.database.tables_erp import BdgPresupuestoDetalleTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in BdgPresupuestoDetalleTable.c}


async def list_presupuesto_detalle(
    client_id: UUID,
    presupuesto_id: Optional[UUID] = None,
    cuenta_id: Optional[UUID] = None,
    centro_costo_id: Optional[UUID] = None,
    mes: Optional[int] = None,
) -> List[Dict[str, Any]]:
    q = select(BdgPresupuestoDetalleTable).where(
        BdgPresupuestoDetalleTable.c.cliente_id == client_id
    )
    if presupuesto_id:
        q = q.where(BdgPresupuestoDetalleTable.c.presupuesto_id == presupuesto_id)
    if cuenta_id:
        q = q.where(BdgPresupuestoDetalleTable.c.cuenta_id == cuenta_id)
    if centro_costo_id:
        q = q.where(BdgPresupuestoDetalleTable.c.centro_costo_id == centro_costo_id)
    if mes is not None:
        q = q.where(BdgPresupuestoDetalleTable.c.mes == mes)
    q = q.order_by(
        BdgPresupuestoDetalleTable.c.presupuesto_id,
        BdgPresupuestoDetalleTable.c.cuenta_id,
        BdgPresupuestoDetalleTable.c.mes,
    )
    return await execute_query(q, client_id=client_id)


async def get_presupuesto_detalle_by_id(
    client_id: UUID, presupuesto_detalle_id: UUID
) -> Optional[Dict[str, Any]]:
    q = select(BdgPresupuestoDetalleTable).where(
        and_(
            BdgPresupuestoDetalleTable.c.cliente_id == client_id,
            BdgPresupuestoDetalleTable.c.presupuesto_detalle_id == presupuesto_detalle_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_presupuesto_detalle(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("presupuesto_detalle_id", uuid4())
    await execute_insert(insert(BdgPresupuestoDetalleTable).values(**payload), client_id=client_id)
    return await get_presupuesto_detalle_by_id(client_id, payload["presupuesto_detalle_id"])


async def update_presupuesto_detalle(
    client_id: UUID, presupuesto_detalle_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("presupuesto_detalle_id", "cliente_id")
    }
    if not payload:
        return await get_presupuesto_detalle_by_id(client_id, presupuesto_detalle_id)
    stmt = update(BdgPresupuestoDetalleTable).where(
        and_(
            BdgPresupuestoDetalleTable.c.cliente_id == client_id,
            BdgPresupuestoDetalleTable.c.presupuesto_detalle_id == presupuesto_detalle_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_presupuesto_detalle_by_id(client_id, presupuesto_detalle_id)
