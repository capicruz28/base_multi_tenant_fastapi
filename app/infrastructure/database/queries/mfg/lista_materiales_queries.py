"""Queries para mfg_lista_materiales (BOM). Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_
from app.infrastructure.database.tables_erp import MfgListaMaterialesTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in MfgListaMaterialesTable.c}


async def list_listas_materiales(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    es_bom_activa: Optional[bool] = None,
    estado: Optional[str] = None,
    buscar: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = select(MfgListaMaterialesTable).where(MfgListaMaterialesTable.c.cliente_id == client_id)
    if empresa_id:
        q = q.where(MfgListaMaterialesTable.c.empresa_id == empresa_id)
    if producto_id:
        q = q.where(MfgListaMaterialesTable.c.producto_id == producto_id)
    if es_bom_activa is not None:
        q = q.where(MfgListaMaterialesTable.c.es_bom_activa == es_bom_activa)
    if estado:
        q = q.where(MfgListaMaterialesTable.c.estado == estado)
    if buscar:
        q = q.where(MfgListaMaterialesTable.c.codigo_bom.ilike(f"%{buscar}%"))
    q = q.order_by(MfgListaMaterialesTable.c.codigo_bom)
    return await execute_query(q, client_id=client_id)


async def get_lista_materiales_by_id(client_id: UUID, bom_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(MfgListaMaterialesTable).where(
        and_(
            MfgListaMaterialesTable.c.cliente_id == client_id,
            MfgListaMaterialesTable.c.bom_id == bom_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_lista_materiales(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("bom_id", uuid4())
    await execute_insert(insert(MfgListaMaterialesTable).values(**payload), client_id=client_id)
    return await get_lista_materiales_by_id(client_id, payload["bom_id"])


async def update_lista_materiales(
    client_id: UUID, bom_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("bom_id", "cliente_id")}
    if not payload:
        return await get_lista_materiales_by_id(client_id, bom_id)
    stmt = update(MfgListaMaterialesTable).where(
        and_(
            MfgListaMaterialesTable.c.cliente_id == client_id,
            MfgListaMaterialesTable.c.bom_id == bom_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_lista_materiales_by_id(client_id, bom_id)
