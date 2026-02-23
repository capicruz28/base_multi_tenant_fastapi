"""
Servicios de aplicación para crm_campana.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.infrastructure.database.queries.crm import (
    list_campanas as _list_campanas,
    get_campana_by_id as _get_campana_by_id,
    create_campana as _create_campana,
    update_campana as _update_campana,
)
from app.modules.crm.presentation.schemas import (
    CampanaCreate,
    CampanaUpdate,
    CampanaRead,
)
from app.core.exceptions import NotFoundError


async def list_campanas(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_campana: Optional[str] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    buscar: Optional[str] = None
) -> List[CampanaRead]:
    """Lista campañas del tenant."""
    rows = await _list_campanas(
        client_id=client_id,
        empresa_id=empresa_id,
        tipo_campana=tipo_campana,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar
    )
    return [CampanaRead(**row) for row in rows]


async def get_campana_by_id(client_id: UUID, campana_id: UUID) -> CampanaRead:
    """Obtiene una campaña por id."""
    row = await _get_campana_by_id(client_id, campana_id)
    if not row:
        raise NotFoundError(f"Campaña {campana_id} no encontrada")
    return CampanaRead(**row)


async def create_campana(client_id: UUID, data: CampanaCreate) -> CampanaRead:
    """Crea una campaña."""
    row = await _create_campana(client_id, data.model_dump(exclude_none=True))
    return CampanaRead(**row)


async def update_campana(
    client_id: UUID, campana_id: UUID, data: CampanaUpdate
) -> CampanaRead:
    """Actualiza una campaña."""
    row = await _update_campana(
        client_id, campana_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Campaña {campana_id} no encontrada")
    return CampanaRead(**row)
