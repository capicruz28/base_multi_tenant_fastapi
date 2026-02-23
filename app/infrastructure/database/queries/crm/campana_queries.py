"""
Queries SQLAlchemy Core para crm_campana.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import date
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import CrmCampanaTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in CrmCampanaTable.c}


async def list_campanas(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_campana: Optional[str] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    buscar: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista campañas del tenant."""
    query = select(CrmCampanaTable).where(
        CrmCampanaTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(CrmCampanaTable.c.empresa_id == empresa_id)
    if tipo_campana:
        query = query.where(CrmCampanaTable.c.tipo_campana == tipo_campana)
    if estado:
        query = query.where(CrmCampanaTable.c.estado == estado)
    if fecha_desde:
        query = query.where(CrmCampanaTable.c.fecha_inicio >= fecha_desde)
    if fecha_hasta:
        query = query.where(CrmCampanaTable.c.fecha_inicio <= fecha_hasta)
    if buscar:
        search_filter = or_(
            CrmCampanaTable.c.nombre.ilike(f"%{buscar}%"),
            CrmCampanaTable.c.codigo_campana.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(CrmCampanaTable.c.fecha_inicio.desc())
    return await execute_query(query, client_id=client_id)


async def get_campana_by_id(client_id: UUID, campana_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una campaña por id."""
    query = select(CrmCampanaTable).where(
        and_(
            CrmCampanaTable.c.cliente_id == client_id,
            CrmCampanaTable.c.campana_id == campana_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_campana(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una campaña."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("campana_id", uuid4())
    stmt = insert(CrmCampanaTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_campana_by_id(client_id, payload["campana_id"])


async def update_campana(
    client_id: UUID, campana_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una campaña."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("campana_id", "cliente_id")
    }
    if not payload:
        return await get_campana_by_id(client_id, campana_id)
    stmt = (
        update(CrmCampanaTable)
        .where(
            and_(
                CrmCampanaTable.c.cliente_id == client_id,
                CrmCampanaTable.c.campana_id == campana_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_campana_by_id(client_id, campana_id)
