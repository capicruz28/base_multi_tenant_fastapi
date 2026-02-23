"""
Servicios de aplicación para log_ruta.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Optional
from uuid import UUID

from app.infrastructure.database.queries.log import (
    list_rutas as _list_rutas,
    get_ruta_by_id as _get_ruta_by_id,
    create_ruta as _create_ruta,
    update_ruta as _update_ruta,
)
from app.modules.log.presentation.schemas import (
    RutaCreate,
    RutaUpdate,
    RutaRead,
)
from app.core.exceptions import NotFoundError


async def list_rutas(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    origen_sucursal_id: Optional[UUID] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None
) -> List[RutaRead]:
    """Lista rutas del tenant."""
    rows = await _list_rutas(
        client_id=client_id,
        empresa_id=empresa_id,
        origen_sucursal_id=origen_sucursal_id,
        solo_activos=solo_activos,
        buscar=buscar
    )
    return [RutaRead(**row) for row in rows]


async def get_ruta_by_id(client_id: UUID, ruta_id: UUID) -> RutaRead:
    """Obtiene una ruta por id. Lanza NotFoundError si no existe."""
    row = await _get_ruta_by_id(client_id, ruta_id)
    if not row:
        raise NotFoundError(f"Ruta {ruta_id} no encontrada")
    return RutaRead(**row)


async def create_ruta(client_id: UUID, data: RutaCreate) -> RutaRead:
    """Crea una ruta."""
    row = await _create_ruta(client_id, data.model_dump(exclude_none=True))
    return RutaRead(**row)


async def update_ruta(
    client_id: UUID, ruta_id: UUID, data: RutaUpdate
) -> RutaRead:
    """Actualiza una ruta. Lanza NotFoundError si no existe."""
    row = await _update_ruta(
        client_id, ruta_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Ruta {ruta_id} no encontrada")
    return RutaRead(**row)
