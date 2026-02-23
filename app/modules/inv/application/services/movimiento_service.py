# app/modules/inv/application/services/movimiento_service.py
"""
Servicio de Movimiento (INV). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.inv import (
    list_movimientos,
    get_movimiento_by_id,
    create_movimiento,
    update_movimiento,
)
from app.modules.inv.presentation.schemas import (
    MovimientoCreate,
    MovimientoUpdate,
    MovimientoRead,
)


def _row_to_read(row: dict) -> MovimientoRead:
    return MovimientoRead(**row)


async def list_movimientos_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_movimiento_id: Optional[UUID] = None,
    almacen_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> List[MovimientoRead]:
    rows = await list_movimientos(
        client_id=client_id,
        empresa_id=empresa_id,
        tipo_movimiento_id=tipo_movimiento_id,
        almacen_id=almacen_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )
    return [_row_to_read(r) for r in rows]


async def get_movimiento_servicio(
    client_id: UUID,
    movimiento_id: UUID,
) -> MovimientoRead:
    row = await get_movimiento_by_id(client_id=client_id, movimiento_id=movimiento_id)
    if not row:
        raise NotFoundError(detail="Movimiento no encontrado")
    return _row_to_read(row)


async def create_movimiento_servicio(
    client_id: UUID,
    data: MovimientoCreate,
) -> MovimientoRead:
    payload = data.model_dump()
    row = await create_movimiento(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_movimiento_servicio(
    client_id: UUID,
    movimiento_id: UUID,
    data: MovimientoUpdate,
) -> MovimientoRead:
    row = await get_movimiento_by_id(client_id=client_id, movimiento_id=movimiento_id)
    if not row:
        raise NotFoundError(detail="Movimiento no encontrado")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_movimiento(client_id=client_id, movimiento_id=movimiento_id, data=payload)
    return _row_to_read(updated)
