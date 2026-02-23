"""Queries para aud_log_auditoria. Filtro tenant: cliente_id. Solo lectura + create (sin update/delete)."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, and_, or_, desc
from app.infrastructure.database.tables_erp import AudLogAuditoriaTable
from app.infrastructure.database.queries_async import execute_query, execute_insert

_COLUMNS = {c.name for c in AudLogAuditoriaTable.c}


async def list_log_auditoria(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    modulo: Optional[str] = None,
    tabla: Optional[str] = None,
    accion: Optional[str] = None,
    usuario_id: Optional[UUID] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    registro_id: Optional[UUID] = None,
    buscar: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    q = select(AudLogAuditoriaTable).where(AudLogAuditoriaTable.c.cliente_id == client_id)
    if empresa_id:
        q = q.where(AudLogAuditoriaTable.c.empresa_id == empresa_id)
    if modulo:
        q = q.where(AudLogAuditoriaTable.c.modulo == modulo)
    if tabla:
        q = q.where(AudLogAuditoriaTable.c.tabla == tabla)
    if accion:
        q = q.where(AudLogAuditoriaTable.c.accion == accion)
    if usuario_id:
        q = q.where(AudLogAuditoriaTable.c.usuario_id == usuario_id)
    if fecha_desde:
        q = q.where(AudLogAuditoriaTable.c.fecha_evento >= fecha_desde)
    if fecha_hasta:
        q = q.where(AudLogAuditoriaTable.c.fecha_evento <= fecha_hasta)
    if registro_id:
        q = q.where(AudLogAuditoriaTable.c.registro_id == registro_id)
    if buscar:
        q = q.where(or_(
            AudLogAuditoriaTable.c.usuario_nombre.ilike(f"%{buscar}%"),
            AudLogAuditoriaTable.c.registro_descripcion.ilike(f"%{buscar}%"),
            AudLogAuditoriaTable.c.observaciones.ilike(f"%{buscar}%"),
        ))
    q = q.order_by(desc(AudLogAuditoriaTable.c.fecha_evento))
    if limit is not None:
        q = q.limit(limit)
    return await execute_query(q, client_id=client_id)


async def get_log_auditoria_by_id(client_id: UUID, log_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(AudLogAuditoriaTable).where(
        and_(
            AudLogAuditoriaTable.c.cliente_id == client_id,
            AudLogAuditoriaTable.c.log_id == log_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_log_auditoria(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("log_id", uuid4())
    await execute_insert(insert(AudLogAuditoriaTable).values(**payload), client_id=client_id)
    return await get_log_auditoria_by_id(client_id, payload["log_id"])
