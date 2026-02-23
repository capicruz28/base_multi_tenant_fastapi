"""
Servicios de aplicación para qms_inspeccion y qms_inspeccion_detalle.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.infrastructure.database.queries.qms import (
    list_inspecciones as _list_inspecciones,
    get_inspeccion_by_id as _get_inspeccion_by_id,
    create_inspeccion as _create_inspeccion,
    update_inspeccion as _update_inspeccion,
    list_inspeccion_detalles as _list_inspeccion_detalles,
    get_inspeccion_detalle_by_id as _get_inspeccion_detalle_by_id,
    create_inspeccion_detalle as _create_inspeccion_detalle,
    update_inspeccion_detalle as _update_inspeccion_detalle,
)
from app.modules.qms.presentation.schemas import (
    InspeccionCreate,
    InspeccionUpdate,
    InspeccionRead,
    InspeccionDetalleCreate,
    InspeccionDetalleUpdate,
    InspeccionDetalleRead,
)
from app.core.exceptions import NotFoundError


async def list_inspecciones(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    plan_inspeccion_id: Optional[UUID] = None,
    resultado: Optional[str] = None,
    lote: Optional[str] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    buscar: Optional[str] = None
) -> List[InspeccionRead]:
    """Lista inspecciones del tenant."""
    rows = await _list_inspecciones(
        client_id=client_id,
        empresa_id=empresa_id,
        producto_id=producto_id,
        plan_inspeccion_id=plan_inspeccion_id,
        resultado=resultado,
        lote=lote,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar
    )
    return [InspeccionRead(**row) for row in rows]


async def get_inspeccion_by_id(client_id: UUID, inspeccion_id: UUID) -> InspeccionRead:
    """Obtiene una inspección por id."""
    row = await _get_inspeccion_by_id(client_id, inspeccion_id)
    if not row:
        raise NotFoundError(f"Inspección {inspeccion_id} no encontrada")
    return InspeccionRead(**row)


async def create_inspeccion(client_id: UUID, data: InspeccionCreate) -> InspeccionRead:
    """Crea una inspección."""
    row = await _create_inspeccion(client_id, data.model_dump(exclude_none=True))
    return InspeccionRead(**row)


async def update_inspeccion(
    client_id: UUID, inspeccion_id: UUID, data: InspeccionUpdate
) -> InspeccionRead:
    """Actualiza una inspección."""
    row = await _update_inspeccion(
        client_id, inspeccion_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Inspección {inspeccion_id} no encontrada")
    return InspeccionRead(**row)


async def list_inspeccion_detalles(
    client_id: UUID, inspeccion_id: UUID
) -> List[InspeccionDetalleRead]:
    """Lista detalles de una inspección."""
    rows = await _list_inspeccion_detalles(client_id, inspeccion_id)
    return [InspeccionDetalleRead(**row) for row in rows]


async def get_inspeccion_detalle_by_id(
    client_id: UUID, inspeccion_detalle_id: UUID
) -> InspeccionDetalleRead:
    """Obtiene un detalle por id."""
    row = await _get_inspeccion_detalle_by_id(client_id, inspeccion_detalle_id)
    if not row:
        raise NotFoundError(f"Detalle de inspección {inspeccion_detalle_id} no encontrado")
    return InspeccionDetalleRead(**row)


async def create_inspeccion_detalle(
    client_id: UUID, data: InspeccionDetalleCreate
) -> InspeccionDetalleRead:
    """Crea un detalle de inspección."""
    row = await _create_inspeccion_detalle(client_id, data.model_dump(exclude_none=True))
    return InspeccionDetalleRead(**row)


async def update_inspeccion_detalle(
    client_id: UUID, inspeccion_detalle_id: UUID, data: InspeccionDetalleUpdate
) -> InspeccionDetalleRead:
    """Actualiza un detalle de inspección."""
    row = await _update_inspeccion_detalle(
        client_id, inspeccion_detalle_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Detalle de inspección {inspeccion_detalle_id} no encontrado")
    return InspeccionDetalleRead(**row)
