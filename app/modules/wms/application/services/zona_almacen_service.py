"""
Servicios de aplicación para wms_zona_almacen.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Optional
from uuid import UUID

from app.infrastructure.database.queries.wms import (
    list_zonas_almacen as _list_zonas_almacen,
    get_zona_almacen_by_id as _get_zona_almacen_by_id,
    create_zona_almacen as _create_zona_almacen,
    update_zona_almacen as _update_zona_almacen,
)
from app.modules.wms.presentation.schemas import (
    ZonaAlmacenCreate,
    ZonaAlmacenUpdate,
    ZonaAlmacenRead,
)
from app.core.exceptions import NotFoundError


async def list_zonas_almacen(
    client_id: UUID,
    almacen_id: Optional[UUID] = None,
    tipo_zona: Optional[str] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None
) -> List[ZonaAlmacenRead]:
    """Lista zonas de almacén del tenant."""
    rows = await _list_zonas_almacen(
        client_id=client_id,
        almacen_id=almacen_id,
        tipo_zona=tipo_zona,
        solo_activos=solo_activos,
        buscar=buscar
    )
    return [ZonaAlmacenRead(**row) for row in rows]


async def get_zona_almacen_by_id(client_id: UUID, zona_id: UUID) -> ZonaAlmacenRead:
    """Obtiene una zona por id. Lanza NotFoundError si no existe."""
    row = await _get_zona_almacen_by_id(client_id, zona_id)
    if not row:
        raise NotFoundError(f"Zona de almacén {zona_id} no encontrada")
    return ZonaAlmacenRead(**row)


async def create_zona_almacen(client_id: UUID, data: ZonaAlmacenCreate) -> ZonaAlmacenRead:
    """Crea una zona de almacén."""
    row = await _create_zona_almacen(client_id, data.model_dump(exclude_none=True))
    return ZonaAlmacenRead(**row)


async def update_zona_almacen(
    client_id: UUID, zona_id: UUID, data: ZonaAlmacenUpdate
) -> ZonaAlmacenRead:
    """Actualiza una zona de almacén. Lanza NotFoundError si no existe."""
    row = await _update_zona_almacen(
        client_id, zona_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Zona de almacén {zona_id} no encontrada")
    return ZonaAlmacenRead(**row)
