"""Queries para bi_reporte. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_
from app.infrastructure.database.tables_erp import BiReporteTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in BiReporteTable.c}


async def list_reporte(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_reporte: Optional[str] = None,
    modulo_origen: Optional[str] = None,
    categoria: Optional[str] = None,
    es_activo: Optional[bool] = None,
    es_publico: Optional[bool] = None,
    buscar: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = select(BiReporteTable).where(BiReporteTable.c.cliente_id == client_id)
    if empresa_id:
        q = q.where(BiReporteTable.c.empresa_id == empresa_id)
    if tipo_reporte:
        q = q.where(BiReporteTable.c.tipo_reporte == tipo_reporte)
    if modulo_origen:
        q = q.where(BiReporteTable.c.modulo_origen == modulo_origen)
    if categoria:
        q = q.where(BiReporteTable.c.categoria == categoria)
    if es_activo is not None:
        q = q.where(BiReporteTable.c.es_activo == es_activo)
    if es_publico is not None:
        q = q.where(BiReporteTable.c.es_publico == es_publico)
    if buscar:
        q = q.where(or_(
            BiReporteTable.c.nombre.ilike(f"%{buscar}%"),
            BiReporteTable.c.codigo_reporte.ilike(f"%{buscar}%"),
        ))
    q = q.order_by(BiReporteTable.c.codigo_reporte)
    return await execute_query(q, client_id=client_id)


async def get_reporte_by_id(client_id: UUID, reporte_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(BiReporteTable).where(
        and_(
            BiReporteTable.c.cliente_id == client_id,
            BiReporteTable.c.reporte_id == reporte_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_reporte(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("reporte_id", uuid4())
    await execute_insert(insert(BiReporteTable).values(**payload), client_id=client_id)
    return await get_reporte_by_id(client_id, payload["reporte_id"])


async def update_reporte(
    client_id: UUID, reporte_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("reporte_id", "cliente_id")
    }
    if not payload:
        return await get_reporte_by_id(client_id, reporte_id)
    stmt = update(BiReporteTable).where(
        and_(
            BiReporteTable.c.cliente_id == client_id,
            BiReporteTable.c.reporte_id == reporte_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_reporte_by_id(client_id, reporte_id)
