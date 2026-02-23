"""Queries para mfg_centro_trabajo. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_
from app.infrastructure.database.tables_erp import MfgCentroTrabajoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in MfgCentroTrabajoTable.c}


async def list_centros_trabajo(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    estado_centro: Optional[str] = None,
    es_activo: Optional[bool] = None,
    buscar: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = select(MfgCentroTrabajoTable).where(MfgCentroTrabajoTable.c.cliente_id == client_id)
    if empresa_id:
        q = q.where(MfgCentroTrabajoTable.c.empresa_id == empresa_id)
    if estado_centro:
        q = q.where(MfgCentroTrabajoTable.c.estado_centro == estado_centro)
    if es_activo is not None:
        q = q.where(MfgCentroTrabajoTable.c.es_activo == es_activo)
    if buscar:
        q = q.where(or_(
            MfgCentroTrabajoTable.c.nombre.ilike(f"%{buscar}%"),
            MfgCentroTrabajoTable.c.codigo.ilike(f"%{buscar}%"),
        ))
    q = q.order_by(MfgCentroTrabajoTable.c.codigo)
    return await execute_query(q, client_id=client_id)


async def get_centro_trabajo_by_id(client_id: UUID, centro_trabajo_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(MfgCentroTrabajoTable).where(
        and_(
            MfgCentroTrabajoTable.c.cliente_id == client_id,
            MfgCentroTrabajoTable.c.centro_trabajo_id == centro_trabajo_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_centro_trabajo(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("centro_trabajo_id", uuid4())
    await execute_insert(insert(MfgCentroTrabajoTable).values(**payload), client_id=client_id)
    return await get_centro_trabajo_by_id(client_id, payload["centro_trabajo_id"])


async def update_centro_trabajo(
    client_id: UUID, centro_trabajo_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("centro_trabajo_id", "cliente_id")}
    if not payload:
        return await get_centro_trabajo_by_id(client_id, centro_trabajo_id)
    stmt = update(MfgCentroTrabajoTable).where(
        and_(
            MfgCentroTrabajoTable.c.cliente_id == client_id,
            MfgCentroTrabajoTable.c.centro_trabajo_id == centro_trabajo_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_centro_trabajo_by_id(client_id, centro_trabajo_id)
