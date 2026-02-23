"""
Servicios de aplicación para wms_stock_ubicacion.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Optional
from uuid import UUID

from app.infrastructure.database.queries.wms import (
    list_stock_ubicaciones as _list_stock_ubicaciones,
    get_stock_ubicacion_by_id as _get_stock_ubicacion_by_id,
    create_stock_ubicacion as _create_stock_ubicacion,
    update_stock_ubicacion as _update_stock_ubicacion,
)
from app.modules.wms.presentation.schemas import (
    StockUbicacionCreate,
    StockUbicacionUpdate,
    StockUbicacionRead,
)
from app.core.exceptions import NotFoundError


async def list_stock_ubicaciones(
    client_id: UUID,
    almacen_id: Optional[UUID] = None,
    ubicacion_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    estado_stock: Optional[str] = None,
    lote: Optional[str] = None
) -> List[StockUbicacionRead]:
    """Lista stock por ubicación del tenant."""
    rows = await _list_stock_ubicaciones(
        client_id=client_id,
        almacen_id=almacen_id,
        ubicacion_id=ubicacion_id,
        producto_id=producto_id,
        estado_stock=estado_stock,
        lote=lote
    )
    return [StockUbicacionRead(**row) for row in rows]


async def get_stock_ubicacion_by_id(client_id: UUID, stock_ubicacion_id: UUID) -> StockUbicacionRead:
    """Obtiene un stock por ubicación por id. Lanza NotFoundError si no existe."""
    row = await _get_stock_ubicacion_by_id(client_id, stock_ubicacion_id)
    if not row:
        raise NotFoundError(f"Stock por ubicación {stock_ubicacion_id} no encontrado")
    return StockUbicacionRead(**row)


async def create_stock_ubicacion(client_id: UUID, data: StockUbicacionCreate) -> StockUbicacionRead:
    """Crea un stock por ubicación."""
    row = await _create_stock_ubicacion(client_id, data.model_dump(exclude_none=True))
    return StockUbicacionRead(**row)


async def update_stock_ubicacion(
    client_id: UUID, stock_ubicacion_id: UUID, data: StockUbicacionUpdate
) -> StockUbicacionRead:
    """Actualiza un stock por ubicación. Lanza NotFoundError si no existe."""
    row = await _update_stock_ubicacion(
        client_id, stock_ubicacion_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Stock por ubicación {stock_ubicacion_id} no encontrado")
    return StockUbicacionRead(**row)
