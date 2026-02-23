"""
Queries SQLAlchemy Core para crm_actividad.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, date
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import CrmActividadTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in CrmActividadTable.c}


async def list_actividades(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    lead_id: Optional[UUID] = None,
    oportunidad_id: Optional[UUID] = None,
    cliente_venta_id: Optional[UUID] = None,
    tipo_actividad: Optional[str] = None,
    usuario_responsable_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    buscar: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista actividades del tenant."""
    query = select(CrmActividadTable).where(
        CrmActividadTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(CrmActividadTable.c.empresa_id == empresa_id)
    if lead_id:
        query = query.where(CrmActividadTable.c.lead_id == lead_id)
    if oportunidad_id:
        query = query.where(CrmActividadTable.c.oportunidad_id == oportunidad_id)
    if cliente_venta_id:
        query = query.where(CrmActividadTable.c.cliente_venta_id == cliente_venta_id)
    if tipo_actividad:
        query = query.where(CrmActividadTable.c.tipo_actividad == tipo_actividad)
    if usuario_responsable_id:
        query = query.where(CrmActividadTable.c.usuario_responsable_id == usuario_responsable_id)
    if estado:
        query = query.where(CrmActividadTable.c.estado == estado)
    if fecha_desde:
        query = query.where(CrmActividadTable.c.fecha_actividad >= fecha_desde)
    if fecha_hasta:
        query = query.where(CrmActividadTable.c.fecha_actividad <= fecha_hasta)
    if buscar:
        search_filter = or_(
            CrmActividadTable.c.asunto.ilike(f"%{buscar}%"),
            CrmActividadTable.c.descripcion.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(CrmActividadTable.c.fecha_actividad.desc())
    return await execute_query(query, client_id=client_id)


async def get_actividad_by_id(client_id: UUID, actividad_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una actividad por id."""
    query = select(CrmActividadTable).where(
        and_(
            CrmActividadTable.c.cliente_id == client_id,
            CrmActividadTable.c.actividad_id == actividad_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_actividad(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una actividad."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("actividad_id", uuid4())
    stmt = insert(CrmActividadTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_actividad_by_id(client_id, payload["actividad_id"])


async def update_actividad(
    client_id: UUID, actividad_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una actividad."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("actividad_id", "cliente_id")
    }
    if not payload:
        return await get_actividad_by_id(client_id, actividad_id)
    stmt = (
        update(CrmActividadTable)
        .where(
            and_(
                CrmActividadTable.c.cliente_id == client_id,
                CrmActividadTable.c.actividad_id == actividad_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_actividad_by_id(client_id, actividad_id)
