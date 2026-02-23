"""Servicio aplicacion tkt_ticket. Calcula tiempo_resolucion_horas en Read."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.tkt import (
    list_ticket as _list,
    get_ticket_by_id as _get,
    create_ticket as _create,
    update_ticket as _update,
)
from app.modules.tkt.presentation.schemas import (
    TicketCreate,
    TicketUpdate,
    TicketRead,
)
from app.core.exceptions import NotFoundError


def _row_to_read(row: dict) -> dict:
    r = dict(row)
    fc = r.get("fecha_creacion")
    fr = r.get("fecha_resolucion")
    if fc and fr and hasattr(fr, "__sub__"):
        try:
            delta = fr - fc
            r["tiempo_resolucion_horas"] = round(delta.total_seconds() / 3600.0, 2)
        except (TypeError, AttributeError):
            r["tiempo_resolucion_horas"] = None
    else:
        r["tiempo_resolucion_horas"] = None
    return r


async def list_ticket(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    categoria: Optional[str] = None,
    asignado_usuario_id: Optional[UUID] = None,
    buscar: Optional[str] = None,
) -> List[TicketRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        estado=estado,
        prioridad=prioridad,
        categoria=categoria,
        asignado_usuario_id=asignado_usuario_id,
        buscar=buscar,
    )
    return [TicketRead(**_row_to_read(r)) for r in rows]


async def get_ticket_by_id(client_id: UUID, ticket_id: UUID) -> TicketRead:
    row = await _get(client_id, ticket_id)
    if not row:
        raise NotFoundError("Ticket no encontrado")
    return TicketRead(**_row_to_read(row))


async def create_ticket(client_id: UUID, data: TicketCreate) -> TicketRead:
    dump = data.model_dump(exclude_none=True)
    row = await _create(client_id, dump)
    return TicketRead(**_row_to_read(row))


async def update_ticket(
    client_id: UUID, ticket_id: UUID, data: TicketUpdate
) -> TicketRead:
    dump = data.model_dump(exclude_none=True)
    row = await _update(client_id, ticket_id, dump)
    if not row:
        raise NotFoundError("Ticket no encontrado")
    return TicketRead(**_row_to_read(row))
