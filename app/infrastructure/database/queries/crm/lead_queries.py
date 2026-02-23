"""
Queries SQLAlchemy Core para crm_lead.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import CrmLeadTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in CrmLeadTable.c}


async def list_leads(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    campana_id: Optional[UUID] = None,
    origen_lead: Optional[str] = None,
    calificacion: Optional[str] = None,
    estado: Optional[str] = None,
    asignado_vendedor_usuario_id: Optional[UUID] = None,
    buscar: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista leads del tenant."""
    query = select(CrmLeadTable).where(
        CrmLeadTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(CrmLeadTable.c.empresa_id == empresa_id)
    if campana_id:
        query = query.where(CrmLeadTable.c.campana_id == campana_id)
    if origen_lead:
        query = query.where(CrmLeadTable.c.origen_lead == origen_lead)
    if calificacion:
        query = query.where(CrmLeadTable.c.calificacion == calificacion)
    if estado:
        query = query.where(CrmLeadTable.c.estado == estado)
    if asignado_vendedor_usuario_id:
        query = query.where(CrmLeadTable.c.asignado_vendedor_usuario_id == asignado_vendedor_usuario_id)
    if buscar:
        search_filter = or_(
            CrmLeadTable.c.nombre_completo.ilike(f"%{buscar}%"),
            CrmLeadTable.c.empresa_nombre.ilike(f"%{buscar}%"),
            CrmLeadTable.c.email.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(CrmLeadTable.c.puntuacion.desc(), CrmLeadTable.c.fecha_creacion.desc())
    return await execute_query(query, client_id=client_id)


async def get_lead_by_id(client_id: UUID, lead_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un lead por id."""
    query = select(CrmLeadTable).where(
        and_(
            CrmLeadTable.c.cliente_id == client_id,
            CrmLeadTable.c.lead_id == lead_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_lead(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un lead."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("lead_id", uuid4())
    stmt = insert(CrmLeadTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_lead_by_id(client_id, payload["lead_id"])


async def update_lead(
    client_id: UUID, lead_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un lead."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("lead_id", "cliente_id")
    }
    if not payload:
        return await get_lead_by_id(client_id, lead_id)
    stmt = (
        update(CrmLeadTable)
        .where(
            and_(
                CrmLeadTable.c.cliente_id == client_id,
                CrmLeadTable.c.lead_id == lead_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_lead_by_id(client_id, lead_id)
