"""Queries para wfl_flujo_trabajo. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_
from app.infrastructure.database.tables_erp import WflFlujoTrabajoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in WflFlujoTrabajoTable.c}


async def list_flujo_trabajo(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_flujo: Optional[str] = None,
    modulo_aplicable: Optional[str] = None,
    es_activo: Optional[bool] = None,
    buscar: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = select(WflFlujoTrabajoTable).where(WflFlujoTrabajoTable.c.cliente_id == client_id)
    if empresa_id:
        q = q.where(WflFlujoTrabajoTable.c.empresa_id == empresa_id)
    if tipo_flujo:
        q = q.where(WflFlujoTrabajoTable.c.tipo_flujo == tipo_flujo)
    if modulo_aplicable:
        q = q.where(WflFlujoTrabajoTable.c.modulo_aplicable == modulo_aplicable)
    if es_activo is not None:
        q = q.where(WflFlujoTrabajoTable.c.es_activo == es_activo)
    if buscar:
        q = q.where(or_(
            WflFlujoTrabajoTable.c.nombre.ilike(f"%{buscar}%"),
            WflFlujoTrabajoTable.c.codigo_flujo.ilike(f"%{buscar}%"),
        ))
    q = q.order_by(WflFlujoTrabajoTable.c.codigo_flujo)
    return await execute_query(q, client_id=client_id)


async def get_flujo_trabajo_by_id(client_id: UUID, flujo_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(WflFlujoTrabajoTable).where(
        and_(
            WflFlujoTrabajoTable.c.cliente_id == client_id,
            WflFlujoTrabajoTable.c.flujo_id == flujo_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_flujo_trabajo(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("flujo_id", uuid4())
    await execute_insert(insert(WflFlujoTrabajoTable).values(**payload), client_id=client_id)
    return await get_flujo_trabajo_by_id(client_id, payload["flujo_id"])


async def update_flujo_trabajo(
    client_id: UUID, flujo_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("flujo_id", "cliente_id")
    }
    if not payload:
        return await get_flujo_trabajo_by_id(client_id, flujo_id)
    stmt = update(WflFlujoTrabajoTable).where(
        and_(
            WflFlujoTrabajoTable.c.cliente_id == client_id,
            WflFlujoTrabajoTable.c.flujo_id == flujo_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_flujo_trabajo_by_id(client_id, flujo_id)
