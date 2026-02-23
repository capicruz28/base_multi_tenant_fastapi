"""
Servicios de aplicación para pos_turno_caja.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.infrastructure.database.queries.pos import (
    list_turnos_caja as _list_turnos_caja,
    get_turno_caja_by_id as _get_turno_caja_by_id,
    create_turno_caja as _create_turno_caja,
    update_turno_caja as _update_turno_caja,
)
from app.modules.pos.presentation.schemas import (
    TurnoCajaCreate,
    TurnoCajaUpdate,
    TurnoCajaRead,
)
from app.core.exceptions import NotFoundError


async def list_turnos_caja(
    client_id: UUID,
    punto_venta_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    cajero_usuario_id: Optional[UUID] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
) -> List[TurnoCajaRead]:
    """Lista turnos de caja del tenant."""
    rows = await _list_turnos_caja(
        client_id=client_id,
        punto_venta_id=punto_venta_id,
        estado=estado,
        cajero_usuario_id=cajero_usuario_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return [TurnoCajaRead(**row) for row in rows]


async def get_turno_caja_by_id(client_id: UUID, turno_id: UUID) -> TurnoCajaRead:
    """Obtiene un turno de caja por id."""
    row = await _get_turno_caja_by_id(client_id, turno_id)
    if not row:
        raise NotFoundError(f"Turno de caja {turno_id} no encontrado")
    return TurnoCajaRead(**row)


async def create_turno_caja(client_id: UUID, data: TurnoCajaCreate) -> TurnoCajaRead:
    """Crea un turno de caja (apertura)."""
    row = await _create_turno_caja(client_id, data.model_dump(exclude_none=True))
    return TurnoCajaRead(**row)


async def update_turno_caja(
    client_id: UUID, turno_id: UUID, data: TurnoCajaUpdate
) -> TurnoCajaRead:
    """Actualiza un turno de caja (ej. cierre)."""
    row = await _update_turno_caja(
        client_id, turno_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Turno de caja {turno_id} no encontrado")
    return TurnoCajaRead(**row)
