"""
Servicios de aplicación para qms_no_conformidad.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.infrastructure.database.queries.qms import (
    list_no_conformidades as _list_no_conformidades,
    get_no_conformidad_by_id as _get_no_conformidad_by_id,
    create_no_conformidad as _create_no_conformidad,
    update_no_conformidad as _update_no_conformidad,
)
from app.modules.qms.presentation.schemas import (
    NoConformidadCreate,
    NoConformidadUpdate,
    NoConformidadRead,
)
from app.core.exceptions import NotFoundError


async def list_no_conformidades(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    origen: Optional[str] = None,
    tipo_nc: Optional[str] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    buscar: Optional[str] = None
) -> List[NoConformidadRead]:
    """Lista no conformidades del tenant."""
    rows = await _list_no_conformidades(
        client_id=client_id,
        empresa_id=empresa_id,
        producto_id=producto_id,
        origen=origen,
        tipo_nc=tipo_nc,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar
    )
    return [NoConformidadRead(**row) for row in rows]


async def get_no_conformidad_by_id(client_id: UUID, no_conformidad_id: UUID) -> NoConformidadRead:
    """Obtiene una no conformidad por id."""
    row = await _get_no_conformidad_by_id(client_id, no_conformidad_id)
    if not row:
        raise NotFoundError(f"No conformidad {no_conformidad_id} no encontrada")
    return NoConformidadRead(**row)


async def create_no_conformidad(client_id: UUID, data: NoConformidadCreate) -> NoConformidadRead:
    """Crea una no conformidad."""
    row = await _create_no_conformidad(client_id, data.model_dump(exclude_none=True))
    return NoConformidadRead(**row)


async def update_no_conformidad(
    client_id: UUID, no_conformidad_id: UUID, data: NoConformidadUpdate
) -> NoConformidadRead:
    """Actualiza una no conformidad."""
    row = await _update_no_conformidad(
        client_id, no_conformidad_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"No conformidad {no_conformidad_id} no encontrada")
    return NoConformidadRead(**row)
