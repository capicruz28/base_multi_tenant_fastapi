"""
Servicios de aplicación para prc_lista_precio y prc_lista_precio_detalle.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.prc import (
    list_listas_precio as _list_listas_precio,
    get_lista_precio_by_id as _get_lista_precio_by_id,
    create_lista_precio as _create_lista_precio,
    update_lista_precio as _update_lista_precio,
    list_lista_precio_detalles as _list_lista_precio_detalles,
    get_lista_precio_detalle_by_id as _get_lista_precio_detalle_by_id,
    create_lista_precio_detalle as _create_lista_precio_detalle,
    update_lista_precio_detalle as _update_lista_precio_detalle,
)
from app.modules.prc.presentation.schemas import (
    ListaPrecioCreate,
    ListaPrecioUpdate,
    ListaPrecioRead,
    ListaPrecioDetalleCreate,
    ListaPrecioDetalleUpdate,
    ListaPrecioDetalleRead,
)


async def list_listas_precio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_lista: Optional[str] = None,
    solo_activos: bool = True,
    solo_vigentes: bool = False,
    buscar: Optional[str] = None,
) -> List[ListaPrecioRead]:
    """Lista listas de precio del tenant."""
    rows = await _list_listas_precio(
        client_id=client_id,
        empresa_id=empresa_id,
        tipo_lista=tipo_lista,
        solo_activos=solo_activos,
        solo_vigentes=solo_vigentes,
        buscar=buscar,
    )
    return [ListaPrecioRead(**row) for row in rows]


async def get_lista_precio_by_id(
    client_id: UUID, lista_precio_id: UUID, empresa_id: Optional[UUID] = None
) -> ListaPrecioRead:
    """Obtiene una lista de precio por id. Lanza NotFoundError si no existe."""
    row = await _get_lista_precio_by_id(client_id, lista_precio_id, empresa_id)
    if not row:
        raise NotFoundError(f"Lista de precio {lista_precio_id} no encontrada")
    return ListaPrecioRead(**row)


async def create_lista_precio(client_id: UUID, data: ListaPrecioCreate) -> ListaPrecioRead:
    """Crea una lista de precio."""
    row = await _create_lista_precio(client_id, data.model_dump(exclude_none=True))
    return ListaPrecioRead(**row)


async def update_lista_precio(
    client_id: UUID,
    lista_precio_id: UUID,
    data: ListaPrecioUpdate,
    empresa_id: Optional[UUID] = None,
) -> ListaPrecioRead:
    """Actualiza una lista de precio. Lanza NotFoundError si no existe."""
    row = await _update_lista_precio(
        client_id,
        lista_precio_id,
        data.model_dump(exclude_none=True),
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(f"Lista de precio {lista_precio_id} no encontrada")
    return ListaPrecioRead(**row)


async def desactivar_lista_precio(
    client_id: UUID, lista_precio_id: UUID, empresa_id: Optional[UUID] = None
) -> None:
    """Baja lógica (es_activo = 0)."""
    row = await _get_lista_precio_by_id(client_id, lista_precio_id, empresa_id)
    if not row:
        raise NotFoundError(f"Lista de precio {lista_precio_id} no encontrada")
    updated = await _update_lista_precio(
        client_id, lista_precio_id, {"es_activo": False}, empresa_id=empresa_id
    )
    if not updated:
        raise NotFoundError(f"Lista de precio {lista_precio_id} no encontrada")


async def reactivar_lista_precio(
    client_id: UUID, lista_precio_id: UUID, empresa_id: Optional[UUID] = None
) -> ListaPrecioRead:
    """Reactiva lista de precio (es_activo = 1)."""
    row = await _get_lista_precio_by_id(client_id, lista_precio_id, empresa_id)
    if not row:
        raise NotFoundError(f"Lista de precio {lista_precio_id} no encontrada")
    updated = await _update_lista_precio(
        client_id, lista_precio_id, {"es_activo": True}, empresa_id=empresa_id
    )
    if not updated:
        raise NotFoundError(f"Lista de precio {lista_precio_id} no encontrada")
    return ListaPrecioRead(**updated)


# ============================================================================
# DETALLES DE LISTA DE PRECIO
# ============================================================================


async def list_lista_precio_detalles(
    client_id: UUID,
    lista_precio_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    solo_activos: bool = True,
    empresa_id: Optional[UUID] = None,
) -> List[ListaPrecioDetalleRead]:
    """Lista detalles de lista de precio del tenant."""
    rows = await _list_lista_precio_detalles(
        client_id=client_id,
        lista_precio_id=lista_precio_id,
        producto_id=producto_id,
        solo_activos=solo_activos,
        empresa_id=empresa_id,
    )
    return [ListaPrecioDetalleRead(**row) for row in rows]


async def get_lista_precio_detalle_by_id(
    client_id: UUID, lista_precio_detalle_id: UUID, empresa_id: Optional[UUID] = None
) -> ListaPrecioDetalleRead:
    """Obtiene un detalle por id. Lanza NotFoundError si no existe."""
    row = await _get_lista_precio_detalle_by_id(client_id, lista_precio_detalle_id, empresa_id)
    if not row:
        raise NotFoundError(f"Detalle de lista de precio {lista_precio_detalle_id} no encontrado")
    return ListaPrecioDetalleRead(**row)


async def create_lista_precio_detalle(
    client_id: UUID, data: ListaPrecioDetalleCreate
) -> ListaPrecioDetalleRead:
    """Crea un detalle de lista de precio. Valida que la cabecera exista y empresa_id coincida."""
    cab = await _get_lista_precio_by_id(client_id, data.lista_precio_id, data.empresa_id)
    if not cab:
        raise NotFoundError(
            "Lista de precio no encontrada para el cliente y la empresa indicados"
        )
    row = await _create_lista_precio_detalle(client_id, data.model_dump(exclude_none=True))
    return ListaPrecioDetalleRead(**row)


async def update_lista_precio_detalle(
    client_id: UUID,
    lista_precio_detalle_id: UUID,
    data: ListaPrecioDetalleUpdate,
    empresa_id: Optional[UUID] = None,
) -> ListaPrecioDetalleRead:
    """Actualiza un detalle de lista de precio. Lanza NotFoundError si no existe."""
    row = await _update_lista_precio_detalle(
        client_id,
        lista_precio_detalle_id,
        data.model_dump(exclude_none=True),
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(f"Detalle de lista de precio {lista_precio_detalle_id} no encontrado")
    return ListaPrecioDetalleRead(**row)
