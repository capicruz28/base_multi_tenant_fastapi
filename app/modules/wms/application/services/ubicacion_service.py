"""
Servicios de aplicación para wms_ubicacion.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Optional
from uuid import UUID

from app.infrastructure.database.queries.wms import (
    list_ubicaciones as _list_ubicaciones,
    get_ubicacion_by_id as _get_ubicacion_by_id,
    create_ubicacion as _create_ubicacion,
    update_ubicacion as _update_ubicacion,
)
from app.modules.wms.presentation.schemas import (
    UbicacionCreate,
    UbicacionUpdate,
    UbicacionRead,
)
from app.core.exceptions import NotFoundError


async def list_ubicaciones(
    client_id: UUID,
    almacen_id: Optional[UUID] = None,
    zona_id: Optional[UUID] = None,
    tipo_ubicacion: Optional[str] = None,
    estado_ubicacion: Optional[str] = None,
    es_ubicacion_picking: Optional[bool] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None
) -> List[UbicacionRead]:
    """Lista ubicaciones del tenant."""
    rows = await _list_ubicaciones(
        client_id=client_id,
        almacen_id=almacen_id,
        zona_id=zona_id,
        tipo_ubicacion=tipo_ubicacion,
        estado_ubicacion=estado_ubicacion,
        es_ubicacion_picking=es_ubicacion_picking,
        solo_activos=solo_activos,
        buscar=buscar
    )
    return [UbicacionRead(**row) for row in rows]


async def get_ubicacion_by_id(client_id: UUID, ubicacion_id: UUID) -> UbicacionRead:
    """Obtiene una ubicación por id. Lanza NotFoundError si no existe."""
    row = await _get_ubicacion_by_id(client_id, ubicacion_id)
    if not row:
        raise NotFoundError(f"Ubicación {ubicacion_id} no encontrada")
    return UbicacionRead(**row)


async def create_ubicacion(client_id: UUID, data: UbicacionCreate) -> UbicacionRead:
    """Crea una ubicación."""
    row = await _create_ubicacion(client_id, data.model_dump(exclude_none=True))
    return UbicacionRead(**row)


async def update_ubicacion(
    client_id: UUID, ubicacion_id: UUID, data: UbicacionUpdate
) -> UbicacionRead:
    """Actualiza una ubicación. Lanza NotFoundError si no existe."""
    row = await _update_ubicacion(
        client_id, ubicacion_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Ubicación {ubicacion_id} no encontrada")
    return UbicacionRead(**row)
