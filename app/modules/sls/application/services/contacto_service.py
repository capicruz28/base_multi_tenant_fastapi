"""
Servicios de aplicación para sls_cliente_contacto.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID

from app.infrastructure.database.queries.sls import (
    list_contactos as _list_contactos,
    get_contacto_by_id as _get_contacto_by_id,
    create_contacto as _create_contacto,
    update_contacto as _update_contacto,
)
from app.modules.sls.presentation.schemas import ClienteContactoCreate, ClienteContactoUpdate, ClienteContactoRead
from app.core.exceptions import NotFoundError


async def list_contactos(
    client_id: UUID,
    cliente_venta_id: Optional[UUID] = None,
    solo_activos: bool = True
) -> List[ClienteContactoRead]:
    """Lista contactos del tenant."""
    rows = await _list_contactos(
        client_id=client_id,
        cliente_venta_id=cliente_venta_id,
        solo_activos=solo_activos
    )
    return [ClienteContactoRead(**row) for row in rows]


async def get_contacto_by_id(client_id: UUID, contacto_id: UUID) -> ClienteContactoRead:
    """Obtiene un contacto por id. Lanza NotFoundError si no existe."""
    row = await _get_contacto_by_id(client_id, contacto_id)
    if not row:
        raise NotFoundError(f"Contacto {contacto_id} no encontrado")
    return ClienteContactoRead(**row)


async def create_contacto(client_id: UUID, data: ClienteContactoCreate) -> ClienteContactoRead:
    """Crea un contacto."""
    row = await _create_contacto(client_id, data.model_dump(exclude_none=True))
    return ClienteContactoRead(**row)


async def update_contacto(
    client_id: UUID, contacto_id: UUID, data: ClienteContactoUpdate
) -> ClienteContactoRead:
    """Actualiza un contacto. Lanza NotFoundError si no existe."""
    row = await _update_contacto(
        client_id, contacto_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Contacto {contacto_id} no encontrado")
    return ClienteContactoRead(**row)
