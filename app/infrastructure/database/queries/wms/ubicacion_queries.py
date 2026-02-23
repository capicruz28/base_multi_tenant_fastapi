"""
Queries SQLAlchemy Core para wms_ubicacion.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import WmsUbicacionTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in WmsUbicacionTable.c}


async def list_ubicaciones(
    client_id: UUID,
    almacen_id: Optional[UUID] = None,
    zona_id: Optional[UUID] = None,
    tipo_ubicacion: Optional[str] = None,
    estado_ubicacion: Optional[str] = None,
    es_ubicacion_picking: Optional[bool] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista ubicaciones del tenant. Siempre filtra por cliente_id."""
    query = select(WmsUbicacionTable).where(
        WmsUbicacionTable.c.cliente_id == client_id
    )
    if almacen_id:
        query = query.where(WmsUbicacionTable.c.almacen_id == almacen_id)
    if zona_id:
        query = query.where(WmsUbicacionTable.c.zona_id == zona_id)
    if tipo_ubicacion:
        query = query.where(WmsUbicacionTable.c.tipo_ubicacion == tipo_ubicacion)
    if estado_ubicacion:
        query = query.where(WmsUbicacionTable.c.estado_ubicacion == estado_ubicacion)
    if es_ubicacion_picking is not None:
        query = query.where(WmsUbicacionTable.c.es_ubicacion_picking == es_ubicacion_picking)
    if solo_activos:
        query = query.where(WmsUbicacionTable.c.es_activo == True)
    if buscar:
        search_filter = or_(
            WmsUbicacionTable.c.codigo_ubicacion.ilike(f"%{buscar}%"),
            WmsUbicacionTable.c.nombre.ilike(f"%{buscar}%"),
            WmsUbicacionTable.c.pasillo.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(WmsUbicacionTable.c.codigo_ubicacion)
    return await execute_query(query, client_id=client_id)


async def get_ubicacion_by_id(client_id: UUID, ubicacion_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una ubicación por id. Exige cliente_id para no cruzar tenants."""
    query = select(WmsUbicacionTable).where(
        and_(
            WmsUbicacionTable.c.cliente_id == client_id,
            WmsUbicacionTable.c.ubicacion_id == ubicacion_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_ubicacion(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una ubicación. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("ubicacion_id", uuid4())
    stmt = insert(WmsUbicacionTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_ubicacion_by_id(client_id, payload["ubicacion_id"])


async def update_ubicacion(
    client_id: UUID, ubicacion_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una ubicación. WHERE incluye cliente_id y ubicacion_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("ubicacion_id", "cliente_id")
    }
    if not payload:
        return await get_ubicacion_by_id(client_id, ubicacion_id)
    stmt = (
        update(WmsUbicacionTable)
        .where(
            and_(
                WmsUbicacionTable.c.cliente_id == client_id,
                WmsUbicacionTable.c.ubicacion_id == ubicacion_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_ubicacion_by_id(client_id, ubicacion_id)
