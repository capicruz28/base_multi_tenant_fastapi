"""
Servicios de aplicación para sls_cliente_direccion.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID

from app.infrastructure.database.queries.sls import (
    list_direcciones as _list_direcciones,
    get_direccion_by_id as _get_direccion_by_id,
    create_direccion as _create_direccion,
    update_direccion as _update_direccion,
)
from app.modules.sls.presentation.schemas import ClienteDireccionCreate, ClienteDireccionUpdate, ClienteDireccionRead
from app.core.exceptions import NotFoundError


async def list_direcciones(
    client_id: UUID,
    cliente_venta_id: Optional[UUID] = None,
    solo_activos: bool = True
) -> List[ClienteDireccionRead]:
    """Lista direcciones del tenant."""
    rows = await _list_direcciones(
        client_id=client_id,
        cliente_venta_id=cliente_venta_id,
        solo_activos=solo_activos
    )
    return [ClienteDireccionRead(**row) for row in rows]


async def get_direccion_by_id(client_id: UUID, direccion_id: UUID) -> ClienteDireccionRead:
    """Obtiene una direccion por id. Lanza NotFoundError si no existe."""
    row = await _get_direccion_by_id(client_id, direccion_id)
    if not row:
        raise NotFoundError(f"Dirección {direccion_id} no encontrada")
    return ClienteDireccionRead(**row)


async def create_direccion(client_id: UUID, data: ClienteDireccionCreate) -> ClienteDireccionRead:
    """Crea una direccion."""
    row = await _create_direccion(client_id, data.model_dump(exclude_none=True))
    return ClienteDireccionRead(**row)


async def update_direccion(
    client_id: UUID, direccion_id: UUID, data: ClienteDireccionUpdate
) -> ClienteDireccionRead:
    """Actualiza una direccion. Lanza NotFoundError si no existe."""
    row = await _update_direccion(
        client_id, direccion_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Dirección {direccion_id} no encontrada")
    return ClienteDireccionRead(**row)
