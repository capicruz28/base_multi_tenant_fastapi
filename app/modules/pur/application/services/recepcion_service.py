# app/modules/pur/application/services/recepcion_service.py
"""
Servicio de Recepción (PUR). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.pur import (
    list_recepciones,
    get_recepcion_by_id,
    create_recepcion,
    update_recepcion,
)
from app.modules.pur.presentation.schemas import (
    RecepcionCreate,
    RecepcionUpdate,
    RecepcionRead,
)


def _row_to_read(row: dict) -> RecepcionRead:
    return RecepcionRead(**row)


async def list_recepciones_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    orden_compra_id: Optional[UUID] = None,
    proveedor_id: Optional[UUID] = None,
    almacen_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> List[RecepcionRead]:
    rows = await list_recepciones(
        client_id=client_id,
        empresa_id=empresa_id,
        orden_compra_id=orden_compra_id,
        proveedor_id=proveedor_id,
        almacen_id=almacen_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )
    return [_row_to_read(r) for r in rows]


async def get_recepcion_servicio(
    client_id: UUID,
    recepcion_id: UUID,
) -> RecepcionRead:
    row = await get_recepcion_by_id(client_id=client_id, recepcion_id=recepcion_id)
    if not row:
        raise NotFoundError(detail="Recepción no encontrada")
    return _row_to_read(row)


async def create_recepcion_servicio(
    client_id: UUID,
    data: RecepcionCreate,
) -> RecepcionRead:
    payload = data.model_dump()
    row = await create_recepcion(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_recepcion_servicio(
    client_id: UUID,
    recepcion_id: UUID,
    data: RecepcionUpdate,
) -> RecepcionRead:
    row = await get_recepcion_by_id(client_id=client_id, recepcion_id=recepcion_id)
    if not row:
        raise NotFoundError(detail="Recepción no encontrada")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_recepcion(client_id=client_id, recepcion_id=recepcion_id, data=payload)
    return _row_to_read(updated)
