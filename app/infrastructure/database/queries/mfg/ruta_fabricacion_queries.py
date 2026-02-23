"""Queries para mfg_ruta_fabricacion. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_
from app.infrastructure.database.tables_erp import MfgRutaFabricacionTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in MfgRutaFabricacionTable.c}


async def list_rutas_fabricacion(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    es_ruta_activa: Optional[bool] = None,
    estado: Optional[str] = None,
    buscar: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = select(MfgRutaFabricacionTable).where(MfgRutaFabricacionTable.c.cliente_id == client_id)
    if empresa_id:
        q = q.where(MfgRutaFabricacionTable.c.empresa_id == empresa_id)
    if producto_id:
        q = q.where(MfgRutaFabricacionTable.c.producto_id == producto_id)
    if es_ruta_activa is not None:
        q = q.where(MfgRutaFabricacionTable.c.es_ruta_activa == es_ruta_activa)
    if estado:
        q = q.where(MfgRutaFabricacionTable.c.estado == estado)
    if buscar:
        q = q.where(or_(
            MfgRutaFabricacionTable.c.nombre.ilike(f"%{buscar}%"),
            MfgRutaFabricacionTable.c.codigo_ruta.ilike(f"%{buscar}%"),
        ))
    q = q.order_by(MfgRutaFabricacionTable.c.codigo_ruta)
    return await execute_query(q, client_id=client_id)


async def get_ruta_fabricacion_by_id(client_id: UUID, ruta_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(MfgRutaFabricacionTable).where(
        and_(
            MfgRutaFabricacionTable.c.cliente_id == client_id,
            MfgRutaFabricacionTable.c.ruta_id == ruta_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_ruta_fabricacion(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("ruta_id", uuid4())
    await execute_insert(insert(MfgRutaFabricacionTable).values(**payload), client_id=client_id)
    return await get_ruta_fabricacion_by_id(client_id, payload["ruta_id"])


async def update_ruta_fabricacion(
    client_id: UUID, ruta_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("ruta_id", "cliente_id")}
    if not payload:
        return await get_ruta_fabricacion_by_id(client_id, ruta_id)
    stmt = update(MfgRutaFabricacionTable).where(
        and_(
            MfgRutaFabricacionTable.c.cliente_id == client_id,
            MfgRutaFabricacionTable.c.ruta_id == ruta_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_ruta_fabricacion_by_id(client_id, ruta_id)
