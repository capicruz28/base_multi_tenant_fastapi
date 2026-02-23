"""Queries para mfg_ruta_fabricacion_detalle. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_
from app.infrastructure.database.tables_erp import MfgRutaFabricacionDetalleTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in MfgRutaFabricacionDetalleTable.c}


async def list_ruta_fabricacion_detalles(
    client_id: UUID,
    ruta_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    q = select(MfgRutaFabricacionDetalleTable).where(MfgRutaFabricacionDetalleTable.c.cliente_id == client_id)
    if ruta_id:
        q = q.where(MfgRutaFabricacionDetalleTable.c.ruta_id == ruta_id)
    q = q.order_by(MfgRutaFabricacionDetalleTable.c.secuencia)
    return await execute_query(q, client_id=client_id)


async def get_ruta_fabricacion_detalle_by_id(
    client_id: UUID, ruta_detalle_id: UUID
) -> Optional[Dict[str, Any]]:
    q = select(MfgRutaFabricacionDetalleTable).where(
        and_(
            MfgRutaFabricacionDetalleTable.c.cliente_id == client_id,
            MfgRutaFabricacionDetalleTable.c.ruta_detalle_id == ruta_detalle_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_ruta_fabricacion_detalle(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("ruta_detalle_id", uuid4())
    await execute_insert(insert(MfgRutaFabricacionDetalleTable).values(**payload), client_id=client_id)
    return await get_ruta_fabricacion_detalle_by_id(client_id, payload["ruta_detalle_id"])


async def update_ruta_fabricacion_detalle(
    client_id: UUID, ruta_detalle_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("ruta_detalle_id", "cliente_id")}
    if not payload:
        return await get_ruta_fabricacion_detalle_by_id(client_id, ruta_detalle_id)
    stmt = update(MfgRutaFabricacionDetalleTable).where(
        and_(
            MfgRutaFabricacionDetalleTable.c.cliente_id == client_id,
            MfgRutaFabricacionDetalleTable.c.ruta_detalle_id == ruta_detalle_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_ruta_fabricacion_detalle_by_id(client_id, ruta_detalle_id)
