"""
Queries SQLAlchemy Core para log_transportista.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import LogTransportistaTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in LogTransportistaTable.c}


async def list_transportistas(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista transportistas del tenant. Siempre filtra por cliente_id."""
    query = select(LogTransportistaTable).where(
        LogTransportistaTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(LogTransportistaTable.c.empresa_id == empresa_id)
    if solo_activos:
        query = query.where(LogTransportistaTable.c.es_activo == True)
    if buscar:
        search_filter = or_(
            LogTransportistaTable.c.razon_social.ilike(f"%{buscar}%"),
            LogTransportistaTable.c.codigo_transportista.ilike(f"%{buscar}%"),
            LogTransportistaTable.c.numero_documento.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(LogTransportistaTable.c.razon_social)
    return await execute_query(query, client_id=client_id)


async def get_transportista_by_id(client_id: UUID, transportista_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un transportista por id. Exige cliente_id para no cruzar tenants."""
    query = select(LogTransportistaTable).where(
        and_(
            LogTransportistaTable.c.cliente_id == client_id,
            LogTransportistaTable.c.transportista_id == transportista_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_transportista(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un transportista. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("transportista_id", uuid4())
    stmt = insert(LogTransportistaTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_transportista_by_id(client_id, payload["transportista_id"])


async def update_transportista(
    client_id: UUID, transportista_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un transportista. WHERE incluye cliente_id y transportista_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("transportista_id", "cliente_id")
    }
    if not payload:
        return await get_transportista_by_id(client_id, transportista_id)
    stmt = (
        update(LogTransportistaTable)
        .where(
            and_(
                LogTransportistaTable.c.cliente_id == client_id,
                LogTransportistaTable.c.transportista_id == transportista_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_transportista_by_id(client_id, transportista_id)
