"""Queries para mfg_operacion. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_
from app.infrastructure.database.tables_erp import MfgOperacionTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in MfgOperacionTable.c}


async def list_operaciones(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    centro_trabajo_id: Optional[UUID] = None,
    es_activo: Optional[bool] = None,
    buscar: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = select(MfgOperacionTable).where(MfgOperacionTable.c.cliente_id == client_id)
    if empresa_id:
        q = q.where(MfgOperacionTable.c.empresa_id == empresa_id)
    if centro_trabajo_id:
        q = q.where(MfgOperacionTable.c.centro_trabajo_id == centro_trabajo_id)
    if es_activo is not None:
        q = q.where(MfgOperacionTable.c.es_activo == es_activo)
    if buscar:
        q = q.where(or_(
            MfgOperacionTable.c.nombre.ilike(f"%{buscar}%"),
            MfgOperacionTable.c.codigo.ilike(f"%{buscar}%"),
        ))
    q = q.order_by(MfgOperacionTable.c.codigo)
    return await execute_query(q, client_id=client_id)


async def get_operacion_by_id(client_id: UUID, operacion_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(MfgOperacionTable).where(
        and_(
            MfgOperacionTable.c.cliente_id == client_id,
            MfgOperacionTable.c.operacion_id == operacion_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_operacion(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("operacion_id", uuid4())
    await execute_insert(insert(MfgOperacionTable).values(**payload), client_id=client_id)
    return await get_operacion_by_id(client_id, payload["operacion_id"])


async def update_operacion(
    client_id: UUID, operacion_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("operacion_id", "cliente_id")}
    if not payload:
        return await get_operacion_by_id(client_id, operacion_id)
    stmt = update(MfgOperacionTable).where(
        and_(
            MfgOperacionTable.c.cliente_id == client_id,
            MfgOperacionTable.c.operacion_id == operacion_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_operacion_by_id(client_id, operacion_id)
