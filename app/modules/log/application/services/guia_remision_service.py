"""
Servicios de aplicación para log_guia_remision y log_guia_remision_detalle.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.infrastructure.database.queries.log import (
    list_guias_remision as _list_guias_remision,
    get_guia_remision_by_id as _get_guia_remision_by_id,
    create_guia_remision as _create_guia_remision,
    update_guia_remision as _update_guia_remision,
    list_guia_remision_detalles as _list_guia_remision_detalles,
    get_guia_remision_detalle_by_id as _get_guia_remision_detalle_by_id,
    create_guia_remision_detalle as _create_guia_remision_detalle,
    update_guia_remision_detalle as _update_guia_remision_detalle,
)
from app.modules.log.presentation.schemas import (
    GuiaRemisionCreate,
    GuiaRemisionUpdate,
    GuiaRemisionRead,
    GuiaRemisionDetalleCreate,
    GuiaRemisionDetalleUpdate,
    GuiaRemisionDetalleRead,
)
from app.core.exceptions import NotFoundError


async def list_guias_remision(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    motivo_traslado: Optional[str] = None,
    transportista_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    buscar: Optional[str] = None
) -> List[GuiaRemisionRead]:
    """Lista guías de remisión del tenant."""
    rows = await _list_guias_remision(
        client_id=client_id,
        empresa_id=empresa_id,
        estado=estado,
        motivo_traslado=motivo_traslado,
        transportista_id=transportista_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar
    )
    return [GuiaRemisionRead(**row) for row in rows]


async def get_guia_remision_by_id(client_id: UUID, guia_remision_id: UUID) -> GuiaRemisionRead:
    """Obtiene una guía de remisión por id. Lanza NotFoundError si no existe."""
    row = await _get_guia_remision_by_id(client_id, guia_remision_id)
    if not row:
        raise NotFoundError(f"Guía de remisión {guia_remision_id} no encontrada")
    return GuiaRemisionRead(**row)


async def create_guia_remision(client_id: UUID, data: GuiaRemisionCreate) -> GuiaRemisionRead:
    """Crea una guía de remisión."""
    row = await _create_guia_remision(client_id, data.model_dump(exclude_none=True))
    return GuiaRemisionRead(**row)


async def update_guia_remision(
    client_id: UUID, guia_remision_id: UUID, data: GuiaRemisionUpdate
) -> GuiaRemisionRead:
    """Actualiza una guía de remisión. Lanza NotFoundError si no existe."""
    row = await _update_guia_remision(
        client_id, guia_remision_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Guía de remisión {guia_remision_id} no encontrada")
    return GuiaRemisionRead(**row)


# ============================================================================
# DETALLES DE GUÍA DE REMISIÓN
# ============================================================================

async def list_guia_remision_detalles(
    client_id: UUID,
    guia_remision_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None
) -> List[GuiaRemisionDetalleRead]:
    """Lista detalles de guía de remisión del tenant."""
    rows = await _list_guia_remision_detalles(
        client_id=client_id,
        guia_remision_id=guia_remision_id,
        producto_id=producto_id
    )
    return [GuiaRemisionDetalleRead(**row) for row in rows]


async def get_guia_remision_detalle_by_id(client_id: UUID, guia_detalle_id: UUID) -> GuiaRemisionDetalleRead:
    """Obtiene un detalle por id. Lanza NotFoundError si no existe."""
    row = await _get_guia_remision_detalle_by_id(client_id, guia_detalle_id)
    if not row:
        raise NotFoundError(f"Detalle de guía de remisión {guia_detalle_id} no encontrado")
    return GuiaRemisionDetalleRead(**row)


async def create_guia_remision_detalle(client_id: UUID, data: GuiaRemisionDetalleCreate) -> GuiaRemisionDetalleRead:
    """Crea un detalle de guía de remisión."""
    row = await _create_guia_remision_detalle(client_id, data.model_dump(exclude_none=True))
    return GuiaRemisionDetalleRead(**row)


async def update_guia_remision_detalle(
    client_id: UUID, guia_detalle_id: UUID, data: GuiaRemisionDetalleUpdate
) -> GuiaRemisionDetalleRead:
    """Actualiza un detalle de guía de remisión. Lanza NotFoundError si no existe."""
    row = await _update_guia_remision_detalle(
        client_id, guia_detalle_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Detalle de guía de remisión {guia_detalle_id} no encontrado")
    return GuiaRemisionDetalleRead(**row)
