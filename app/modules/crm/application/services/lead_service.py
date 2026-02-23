"""
Servicios de aplicación para crm_lead.
"""
from typing import List, Optional
from uuid import UUID

from app.infrastructure.database.queries.crm import (
    list_leads as _list_leads,
    get_lead_by_id as _get_lead_by_id,
    create_lead as _create_lead,
    update_lead as _update_lead,
)
from app.modules.crm.presentation.schemas import (
    LeadCreate,
    LeadUpdate,
    LeadRead,
)
from app.core.exceptions import NotFoundError


async def list_leads(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    campana_id: Optional[UUID] = None,
    origen_lead: Optional[str] = None,
    calificacion: Optional[str] = None,
    estado: Optional[str] = None,
    asignado_vendedor_usuario_id: Optional[UUID] = None,
    buscar: Optional[str] = None
) -> List[LeadRead]:
    """Lista leads del tenant."""
    rows = await _list_leads(
        client_id=client_id,
        empresa_id=empresa_id,
        campana_id=campana_id,
        origen_lead=origen_lead,
        calificacion=calificacion,
        estado=estado,
        asignado_vendedor_usuario_id=asignado_vendedor_usuario_id,
        buscar=buscar
    )
    return [LeadRead(**row) for row in rows]


async def get_lead_by_id(client_id: UUID, lead_id: UUID) -> LeadRead:
    """Obtiene un lead por id."""
    row = await _get_lead_by_id(client_id, lead_id)
    if not row:
        raise NotFoundError(f"Lead {lead_id} no encontrado")
    return LeadRead(**row)


async def create_lead(client_id: UUID, data: LeadCreate) -> LeadRead:
    """Crea un lead."""
    row = await _create_lead(client_id, data.model_dump(exclude_none=True))
    return LeadRead(**row)


async def update_lead(
    client_id: UUID, lead_id: UUID, data: LeadUpdate
) -> LeadRead:
    """Actualiza un lead."""
    row = await _update_lead(
        client_id, lead_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Lead {lead_id} no encontrado")
    return LeadRead(**row)
