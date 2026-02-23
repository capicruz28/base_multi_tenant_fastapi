"""
Servicios de aplicación para sls_cliente.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID

from app.infrastructure.database.queries.sls import (
    list_clientes as _list_clientes,
    get_cliente_by_id as _get_cliente_by_id,
    create_cliente as _create_cliente,
    update_cliente as _update_cliente,
)
from app.modules.sls.presentation.schemas import ClienteCreate, ClienteUpdate, ClienteRead
from app.core.exceptions import NotFoundError


async def list_clientes(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
    vendedor_usuario_id: Optional[UUID] = None
) -> List[ClienteRead]:
    """Lista clientes del tenant."""
    rows = await _list_clientes(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
        buscar=buscar,
        vendedor_usuario_id=vendedor_usuario_id
    )
    return [ClienteRead(**row) for row in rows]


async def get_cliente_by_id(client_id: UUID, cliente_venta_id: UUID) -> ClienteRead:
    """Obtiene un cliente por id. Lanza NotFoundError si no existe."""
    row = await _get_cliente_by_id(client_id, cliente_venta_id)
    if not row:
        raise NotFoundError(f"Cliente {cliente_venta_id} no encontrado")
    return ClienteRead(**row)


async def create_cliente(client_id: UUID, data: ClienteCreate) -> ClienteRead:
    """Crea un cliente."""
    row = await _create_cliente(client_id, data.model_dump(exclude_none=True))
    return ClienteRead(**row)


async def update_cliente(
    client_id: UUID, cliente_venta_id: UUID, data: ClienteUpdate
) -> ClienteRead:
    """Actualiza un cliente. Lanza NotFoundError si no existe."""
    row = await _update_cliente(
        client_id, cliente_venta_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Cliente {cliente_venta_id} no encontrado")
    return ClienteRead(**row)
