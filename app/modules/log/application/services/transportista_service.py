"""
Servicios de aplicación para log_transportista.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Optional
from uuid import UUID

from app.infrastructure.database.queries.log import (
    list_transportistas as _list_transportistas,
    get_transportista_by_id as _get_transportista_by_id,
    create_transportista as _create_transportista,
    update_transportista as _update_transportista,
)
from app.modules.log.presentation.schemas import (
    TransportistaCreate,
    TransportistaUpdate,
    TransportistaRead,
)
from app.core.exceptions import NotFoundError


async def list_transportistas(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None
) -> List[TransportistaRead]:
    """Lista transportistas del tenant."""
    rows = await _list_transportistas(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
        buscar=buscar
    )
    return [TransportistaRead(**row) for row in rows]


async def get_transportista_by_id(client_id: UUID, transportista_id: UUID) -> TransportistaRead:
    """Obtiene un transportista por id. Lanza NotFoundError si no existe."""
    row = await _get_transportista_by_id(client_id, transportista_id)
    if not row:
        raise NotFoundError(f"Transportista {transportista_id} no encontrado")
    return TransportistaRead(**row)


async def create_transportista(client_id: UUID, data: TransportistaCreate) -> TransportistaRead:
    """Crea un transportista."""
    row = await _create_transportista(client_id, data.model_dump(exclude_none=True))
    return TransportistaRead(**row)


async def update_transportista(
    client_id: UUID, transportista_id: UUID, data: TransportistaUpdate
) -> TransportistaRead:
    """Actualiza un transportista. Lanza NotFoundError si no existe."""
    row = await _update_transportista(
        client_id, transportista_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Transportista {transportista_id} no encontrado")
    return TransportistaRead(**row)
