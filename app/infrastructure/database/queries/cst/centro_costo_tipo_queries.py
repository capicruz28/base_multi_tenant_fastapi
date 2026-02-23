"""Queries para cst_centro_costo_tipo. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_
from app.infrastructure.database.tables_erp import CstCentroCostoTipoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in CstCentroCostoTipoTable.c}


async def list_centro_costo_tipo(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_clasificacion: Optional[str] = None,
    es_activo: Optional[bool] = None,
    buscar: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = select(CstCentroCostoTipoTable).where(CstCentroCostoTipoTable.c.cliente_id == client_id)
    if empresa_id:
        q = q.where(CstCentroCostoTipoTable.c.empresa_id == empresa_id)
    if tipo_clasificacion:
        q = q.where(CstCentroCostoTipoTable.c.tipo_clasificacion == tipo_clasificacion)
    if es_activo is not None:
        q = q.where(CstCentroCostoTipoTable.c.es_activo == es_activo)
    if buscar:
        q = q.where(or_(
            CstCentroCostoTipoTable.c.nombre.ilike(f"%{buscar}%"),
            CstCentroCostoTipoTable.c.codigo.ilike(f"%{buscar}%"),
        ))
    q = q.order_by(CstCentroCostoTipoTable.c.codigo)
    return await execute_query(q, client_id=client_id)


async def get_centro_costo_tipo_by_id(client_id: UUID, cc_tipo_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(CstCentroCostoTipoTable).where(
        and_(
            CstCentroCostoTipoTable.c.cliente_id == client_id,
            CstCentroCostoTipoTable.c.cc_tipo_id == cc_tipo_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_centro_costo_tipo(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("cc_tipo_id", uuid4())
    await execute_insert(insert(CstCentroCostoTipoTable).values(**payload), client_id=client_id)
    return await get_centro_costo_tipo_by_id(client_id, payload["cc_tipo_id"])


async def update_centro_costo_tipo(
    client_id: UUID, cc_tipo_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("cc_tipo_id", "cliente_id")}
    if not payload:
        return await get_centro_costo_tipo_by_id(client_id, cc_tipo_id)
    stmt = update(CstCentroCostoTipoTable).where(
        and_(
            CstCentroCostoTipoTable.c.cliente_id == client_id,
            CstCentroCostoTipoTable.c.cc_tipo_id == cc_tipo_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_centro_costo_tipo_by_id(client_id, cc_tipo_id)
