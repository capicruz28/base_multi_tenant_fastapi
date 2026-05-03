"""
Servicio de Recepción Detalle (PUR). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.modules.org.application.services.empresa_service import get_empresa_servicio
from app.infrastructure.database.queries.pur import (
    list_recepciones_detalle,
    get_recepcion_detalle_by_id,
    create_recepcion_detalle,
    update_recepcion_detalle,
)
from app.modules.pur.presentation.schemas import (
    RecepcionDetalleCreate,
    RecepcionDetalleUpdate,
    RecepcionDetalleRead,
)


def _row_to_read(row: dict) -> RecepcionDetalleRead:
    return RecepcionDetalleRead(**row)


async def list_recepciones_detalle_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    recepcion_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
) -> List[RecepcionDetalleRead]:
    rows = await list_recepciones_detalle(
        client_id=client_id,
        empresa_id=empresa_id,
        recepcion_id=recepcion_id,
        producto_id=producto_id,
    )
    return [_row_to_read(r) for r in rows]


async def get_recepcion_detalle_servicio(
    client_id: UUID,
    recepcion_detalle_id: UUID,
) -> RecepcionDetalleRead:
    row = await get_recepcion_detalle_by_id(
        client_id=client_id,
        recepcion_detalle_id=recepcion_detalle_id,
    )
    if not row:
        raise NotFoundError(detail="Detalle de recepción no encontrado")
    return _row_to_read(row)


async def create_recepcion_detalle_servicio(
    client_id: UUID,
    data: RecepcionDetalleCreate,
) -> RecepcionDetalleRead:
    await get_empresa_servicio(client_id=client_id, empresa_id=data.empresa_id)
    payload = data.model_dump()
    row = await create_recepcion_detalle(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_recepcion_detalle_servicio(
    client_id: UUID,
    recepcion_detalle_id: UUID,
    data: RecepcionDetalleUpdate,
) -> RecepcionDetalleRead:
    row = await get_recepcion_detalle_by_id(
        client_id=client_id,
        recepcion_detalle_id=recepcion_detalle_id,
    )
    if not row:
        raise NotFoundError(detail="Detalle de recepción no encontrado")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_recepcion_detalle(
        client_id=client_id,
        recepcion_detalle_id=recepcion_detalle_id,
        data=payload,
    )
    return _row_to_read(updated)
