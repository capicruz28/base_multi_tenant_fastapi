"""
Servicios de aplicación para crm_oportunidad.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.infrastructure.database.queries.crm import (
    list_oportunidades as _list_oportunidades,
    get_oportunidad_by_id as _get_oportunidad_by_id,
    create_oportunidad as _create_oportunidad,
    update_oportunidad as _update_oportunidad,
)
from app.modules.crm.presentation.schemas import (
    OportunidadCreate,
    OportunidadUpdate,
    OportunidadRead,
)
from app.core.exceptions import NotFoundError


async def list_oportunidades(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    cliente_venta_id: Optional[UUID] = None,
    lead_id: Optional[UUID] = None,
    campana_id: Optional[UUID] = None,
    vendedor_usuario_id: Optional[UUID] = None,
    etapa: Optional[str] = None,
    estado: Optional[str] = None,
    tipo_oportunidad: Optional[str] = None,
    fecha_cierre_desde: Optional[date] = None,
    fecha_cierre_hasta: Optional[date] = None,
    buscar: Optional[str] = None
) -> List[OportunidadRead]:
    """Lista oportunidades del tenant."""
    rows = await _list_oportunidades(
        client_id=client_id,
        empresa_id=empresa_id,
        cliente_venta_id=cliente_venta_id,
        lead_id=lead_id,
        campana_id=campana_id,
        vendedor_usuario_id=vendedor_usuario_id,
        etapa=etapa,
        estado=estado,
        tipo_oportunidad=tipo_oportunidad,
        fecha_cierre_desde=fecha_cierre_desde,
        fecha_cierre_hasta=fecha_cierre_hasta,
        buscar=buscar
    )
    return [OportunidadRead(**row) for row in rows]


async def get_oportunidad_by_id(client_id: UUID, oportunidad_id: UUID) -> OportunidadRead:
    """Obtiene una oportunidad por id."""
    row = await _get_oportunidad_by_id(client_id, oportunidad_id)
    if not row:
        raise NotFoundError(f"Oportunidad {oportunidad_id} no encontrada")
    return OportunidadRead(**row)


async def create_oportunidad(client_id: UUID, data: OportunidadCreate) -> OportunidadRead:
    """Crea una oportunidad."""
    row = await _create_oportunidad(client_id, data.model_dump(exclude_none=True))
    return OportunidadRead(**row)


async def update_oportunidad(
    client_id: UUID, oportunidad_id: UUID, data: OportunidadUpdate
) -> OportunidadRead:
    """Actualiza una oportunidad."""
    row = await _update_oportunidad(
        client_id, oportunidad_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Oportunidad {oportunidad_id} no encontrada")
    return OportunidadRead(**row)
