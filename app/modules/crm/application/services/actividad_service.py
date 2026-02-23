"""
Servicios de aplicación para crm_actividad.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.infrastructure.database.queries.crm import (
    list_actividades as _list_actividades,
    get_actividad_by_id as _get_actividad_by_id,
    create_actividad as _create_actividad,
    update_actividad as _update_actividad,
)
from app.modules.crm.presentation.schemas import (
    ActividadCreate,
    ActividadUpdate,
    ActividadRead,
)
from app.core.exceptions import NotFoundError


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
) -> List[ActividadRead]:
    """Lista actividades del tenant."""
    rows = await _list_actividades(
        client_id=client_id,
        empresa_id=empresa_id,
        lead_id=lead_id,
        oportunidad_id=oportunidad_id,
        cliente_venta_id=cliente_venta_id,
        tipo_actividad=tipo_actividad,
        usuario_responsable_id=usuario_responsable_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar
    )
    return [ActividadRead(**row) for row in rows]


async def get_actividad_by_id(client_id: UUID, actividad_id: UUID) -> ActividadRead:
    """Obtiene una actividad por id."""
    row = await _get_actividad_by_id(client_id, actividad_id)
    if not row:
        raise NotFoundError(f"Actividad {actividad_id} no encontrada")
    return ActividadRead(**row)


async def create_actividad(client_id: UUID, data: ActividadCreate) -> ActividadRead:
    """Crea una actividad."""
    row = await _create_actividad(client_id, data.model_dump(exclude_none=True))
    return ActividadRead(**row)


async def update_actividad(
    client_id: UUID, actividad_id: UUID, data: ActividadUpdate
) -> ActividadRead:
    """Actualiza una actividad."""
    row = await _update_actividad(
        client_id, actividad_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Actividad {actividad_id} no encontrada")
    return ActividadRead(**row)
