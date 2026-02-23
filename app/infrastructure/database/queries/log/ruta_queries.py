"""
Queries SQLAlchemy Core para log_ruta.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import LogRutaTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in LogRutaTable.c}


async def list_rutas(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    origen_sucursal_id: Optional[UUID] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista rutas del tenant. Siempre filtra por cliente_id."""
    query = select(LogRutaTable).where(
        LogRutaTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(LogRutaTable.c.empresa_id == empresa_id)
    if origen_sucursal_id:
        query = query.where(LogRutaTable.c.origen_sucursal_id == origen_sucursal_id)
    if solo_activos:
        query = query.where(LogRutaTable.c.es_activo == True)
    if buscar:
        search_filter = or_(
            LogRutaTable.c.nombre_ruta.ilike(f"%{buscar}%"),
            LogRutaTable.c.codigo_ruta.ilike(f"%{buscar}%"),
            LogRutaTable.c.destino_descripcion.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(LogRutaTable.c.nombre_ruta)
    return await execute_query(query, client_id=client_id)


async def get_ruta_by_id(client_id: UUID, ruta_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una ruta por id. Exige cliente_id para no cruzar tenants."""
    query = select(LogRutaTable).where(
        and_(
            LogRutaTable.c.cliente_id == client_id,
            LogRutaTable.c.ruta_id == ruta_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_ruta(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una ruta. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("ruta_id", uuid4())
    stmt = insert(LogRutaTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_ruta_by_id(client_id, payload["ruta_id"])


async def update_ruta(
    client_id: UUID, ruta_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una ruta. WHERE incluye cliente_id y ruta_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("ruta_id", "cliente_id")
    }
    if not payload:
        return await get_ruta_by_id(client_id, ruta_id)
    stmt = (
        update(LogRutaTable)
        .where(
            and_(
                LogRutaTable.c.cliente_id == client_id,
                LogRutaTable.c.ruta_id == ruta_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_ruta_by_id(client_id, ruta_id)
