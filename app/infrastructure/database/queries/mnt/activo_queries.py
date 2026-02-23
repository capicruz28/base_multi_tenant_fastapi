"""Queries para mnt_activo. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_
from app.infrastructure.database.tables_erp import MntActivoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in MntActivoTable.c}


async def list_activo(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_activo: Optional[str] = None,
    estado_activo: Optional[str] = None,
    criticidad: Optional[str] = None,
    es_activo: Optional[bool] = None,
    buscar: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = select(MntActivoTable).where(MntActivoTable.c.cliente_id == client_id)
    if empresa_id:
        q = q.where(MntActivoTable.c.empresa_id == empresa_id)
    if tipo_activo:
        q = q.where(MntActivoTable.c.tipo_activo == tipo_activo)
    if estado_activo:
        q = q.where(MntActivoTable.c.estado_activo == estado_activo)
    if criticidad:
        q = q.where(MntActivoTable.c.criticidad == criticidad)
    if es_activo is not None:
        q = q.where(MntActivoTable.c.es_activo == es_activo)
    if buscar:
        q = q.where(or_(
            MntActivoTable.c.nombre.ilike(f"%{buscar}%"),
            MntActivoTable.c.codigo_activo.ilike(f"%{buscar}%"),
        ))
    q = q.order_by(MntActivoTable.c.codigo_activo)
    return await execute_query(q, client_id=client_id)


async def get_activo_by_id(client_id: UUID, activo_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(MntActivoTable).where(
        and_(
            MntActivoTable.c.cliente_id == client_id,
            MntActivoTable.c.activo_id == activo_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_activo(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("activo_id", uuid4())
    await execute_insert(insert(MntActivoTable).values(**payload), client_id=client_id)
    return await get_activo_by_id(client_id, payload["activo_id"])


async def update_activo(
    client_id: UUID, activo_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("activo_id", "cliente_id")}
    if not payload:
        return await get_activo_by_id(client_id, activo_id)
    stmt = update(MntActivoTable).where(
        and_(
            MntActivoTable.c.cliente_id == client_id,
            MntActivoTable.c.activo_id == activo_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_activo_by_id(client_id, activo_id)
