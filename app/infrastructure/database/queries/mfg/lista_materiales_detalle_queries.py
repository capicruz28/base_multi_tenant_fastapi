"""Queries para mfg_lista_materiales_detalle. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_
from app.infrastructure.database.tables_erp import MfgListaMaterialesDetalleTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in MfgListaMaterialesDetalleTable.c}


async def list_lista_materiales_detalles(
    client_id: UUID,
    bom_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    q = select(MfgListaMaterialesDetalleTable).where(MfgListaMaterialesDetalleTable.c.cliente_id == client_id)
    if bom_id:
        q = q.where(MfgListaMaterialesDetalleTable.c.bom_id == bom_id)
    q = q.order_by(MfgListaMaterialesDetalleTable.c.secuencia, MfgListaMaterialesDetalleTable.c.bom_detalle_id)
    return await execute_query(q, client_id=client_id)


async def get_lista_materiales_detalle_by_id(
    client_id: UUID, bom_detalle_id: UUID
) -> Optional[Dict[str, Any]]:
    q = select(MfgListaMaterialesDetalleTable).where(
        and_(
            MfgListaMaterialesDetalleTable.c.cliente_id == client_id,
            MfgListaMaterialesDetalleTable.c.bom_detalle_id == bom_detalle_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_lista_materiales_detalle(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("bom_detalle_id", uuid4())
    await execute_insert(insert(MfgListaMaterialesDetalleTable).values(**payload), client_id=client_id)
    return await get_lista_materiales_detalle_by_id(client_id, payload["bom_detalle_id"])


async def update_lista_materiales_detalle(
    client_id: UUID, bom_detalle_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("bom_detalle_id", "cliente_id")}
    if not payload:
        return await get_lista_materiales_detalle_by_id(client_id, bom_detalle_id)
    stmt = update(MfgListaMaterialesDetalleTable).where(
        and_(
            MfgListaMaterialesDetalleTable.c.cliente_id == client_id,
            MfgListaMaterialesDetalleTable.c.bom_detalle_id == bom_detalle_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_lista_materiales_detalle_by_id(client_id, bom_detalle_id)
