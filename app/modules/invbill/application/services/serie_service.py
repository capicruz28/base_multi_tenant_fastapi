"""
Servicios de aplicación para invbill_serie_comprobante.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID

from app.infrastructure.database.queries.invbill import (
    list_series as _list_series,
    get_serie_by_id as _get_serie_by_id,
    create_serie as _create_serie,
    update_serie as _update_serie,
)
from app.modules.invbill.presentation.schemas import SerieComprobanteCreate, SerieComprobanteUpdate, SerieComprobanteRead
from app.core.exceptions import NotFoundError


async def list_series(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_comprobante: Optional[str] = None,
    solo_activos: bool = True
) -> List[SerieComprobanteRead]:
    """Lista series de comprobantes del tenant."""
    rows = await _list_series(
        client_id=client_id,
        empresa_id=empresa_id,
        tipo_comprobante=tipo_comprobante,
        solo_activos=solo_activos
    )
    return [SerieComprobanteRead(**row) for row in rows]


async def get_serie_by_id(client_id: UUID, serie_id: UUID) -> SerieComprobanteRead:
    """Obtiene una serie por id. Lanza NotFoundError si no existe."""
    row = await _get_serie_by_id(client_id, serie_id)
    if not row:
        raise NotFoundError(f"Serie {serie_id} no encontrada")
    return SerieComprobanteRead(**row)


async def create_serie(client_id: UUID, data: SerieComprobanteCreate) -> SerieComprobanteRead:
    """Crea una serie."""
    row = await _create_serie(client_id, data.model_dump(exclude_none=True))
    return SerieComprobanteRead(**row)


async def update_serie(
    client_id: UUID, serie_id: UUID, data: SerieComprobanteUpdate
) -> SerieComprobanteRead:
    """Actualiza una serie. Lanza NotFoundError si no existe."""
    row = await _update_serie(
        client_id, serie_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Serie {serie_id} no encontrada")
    return SerieComprobanteRead(**row)
