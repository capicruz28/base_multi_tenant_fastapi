"""
Queries SQLAlchemy Core para wms_zona_almacen.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import WmsZonaAlmacenTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in WmsZonaAlmacenTable.c}


async def list_zonas_almacen(
    client_id: UUID,
    almacen_id: Optional[UUID] = None,
    tipo_zona: Optional[str] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista zonas de almacén del tenant. Siempre filtra por cliente_id."""
    query = select(WmsZonaAlmacenTable).where(
        WmsZonaAlmacenTable.c.cliente_id == client_id
    )
    if almacen_id:
        query = query.where(WmsZonaAlmacenTable.c.almacen_id == almacen_id)
    if tipo_zona:
        query = query.where(WmsZonaAlmacenTable.c.tipo_zona == tipo_zona)
    if solo_activos:
        query = query.where(WmsZonaAlmacenTable.c.es_activo == True)
    if buscar:
        search_filter = or_(
            WmsZonaAlmacenTable.c.nombre.ilike(f"%{buscar}%"),
            WmsZonaAlmacenTable.c.codigo.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(WmsZonaAlmacenTable.c.nombre)
    return await execute_query(query, client_id=client_id)


async def get_zona_almacen_by_id(client_id: UUID, zona_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una zona por id. Exige cliente_id para no cruzar tenants."""
    query = select(WmsZonaAlmacenTable).where(
        and_(
            WmsZonaAlmacenTable.c.cliente_id == client_id,
            WmsZonaAlmacenTable.c.zona_id == zona_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_zona_almacen(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una zona de almacén. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("zona_id", uuid4())
    stmt = insert(WmsZonaAlmacenTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_zona_almacen_by_id(client_id, payload["zona_id"])


async def update_zona_almacen(
    client_id: UUID, zona_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una zona de almacén. WHERE incluye cliente_id y zona_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("zona_id", "cliente_id")
    }
    if not payload:
        return await get_zona_almacen_by_id(client_id, zona_id)
    stmt = (
        update(WmsZonaAlmacenTable)
        .where(
            and_(
                WmsZonaAlmacenTable.c.cliente_id == client_id,
                WmsZonaAlmacenTable.c.zona_id == zona_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_zona_almacen_by_id(client_id, zona_id)
