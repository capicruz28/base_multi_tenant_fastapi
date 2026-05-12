"""Servicio aplicacion tkt_ticket. Calcula tiempo_resolucion_horas en Read."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.tkt import (
    list_ticket as _list,
    get_ticket_by_id as _get,
    create_ticket as _create,
    update_ticket as _update,
    assign_ticket_transition as _assign_transition,
    iniciar_ticket_transition as _iniciar_transition,
    resolver_ticket_transition as _resolver_transition,
    cerrar_ticket_transition as _cerrar_transition,
)
from app.modules.tkt.presentation.schemas import (
    TicketCreate,
    TicketUpdate,
    TicketRead,
)
from app.core.exceptions import NotFoundError, ValidationError


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


def _norm_estado(v: Optional[str]) -> str:
    return (v or "").strip().lower()


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


async def get_ticket_by_id(
    client_id: UUID, ticket_id: UUID, empresa_id: Optional[UUID] = None
) -> TicketRead:
    row = await _get(client_id, ticket_id, empresa_id=empresa_id)
    if not row:
        raise NotFoundError("Ticket no encontrado")
    return TicketRead(**_row_to_read(row))


async def create_ticket(client_id: UUID, data: TicketCreate) -> TicketRead:
    dump = data.model_dump(exclude_none=True)
    row = await _create(client_id, dump)
    return TicketRead(**_row_to_read(row))


async def update_ticket(
    client_id: UUID,
    ticket_id: UUID,
    data: TicketUpdate,
    empresa_id: Optional[UUID] = None,
) -> TicketRead:
    current = await _get(client_id, ticket_id, empresa_id=empresa_id)
    if not current:
        raise NotFoundError("Ticket no encontrado")
    st = _norm_estado(current.get("estado"))
    if st not in ("abierto", "asignado"):
        raise ValidationError(
            "Solo se puede editar un ticket en estado abierto o asignado."
        )
    dump = data.model_dump(exclude_none=True)
    if "estado" in dump and dump["estado"] is not None:
        if _norm_estado(dump["estado"]) != st:
            raise ValidationError(
                "Los cambios de estado deben realizarse mediante los endpoints de transición."
            )
    row = await _update(client_id, ticket_id, dump, empresa_id=empresa_id)
    if not row:
        raise NotFoundError("Ticket no encontrado")
    return TicketRead(**_row_to_read(row))


async def assign_ticket(
    client_id: UUID,
    ticket_id: UUID,
    asignado_usuario_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> TicketRead:
    current = await _get(client_id, ticket_id, empresa_id=empresa_id)
    if not current:
        raise NotFoundError("Ticket no encontrado")
    st = _norm_estado(current.get("estado"))
    if st == "asignado":
        actual = current.get("asignado_usuario_id")
        if actual == asignado_usuario_id:
            return TicketRead(**_row_to_read(current))
        raise ValidationError("El ticket ya está asignado a otro usuario.")
    if st != "abierto":
        raise ValidationError("Solo se puede asignar un ticket en estado abierto.")
    now = datetime.utcnow()
    row = await _assign_transition(
        client_id,
        ticket_id,
        asignado_usuario_id,
        now,
        empresa_id=empresa_id,
    )
    if row:
        return TicketRead(**_row_to_read(row))
    # Si falló, intentar inferir si cambió de estado por carrera
    cur = await _get(client_id, ticket_id, empresa_id=empresa_id)
    if cur and _norm_estado(cur.get("estado")) == "abierto":
        raise ValidationError(
            "No se pudo asignar el ticket; intente nuevamente o verifique el estado."
        )
    raise ValidationError("Solo se puede asignar un ticket en estado abierto.")


async def iniciar_ticket(
    client_id: UUID, ticket_id: UUID, empresa_id: Optional[UUID] = None
) -> TicketRead:
    current = await _get(client_id, ticket_id, empresa_id=empresa_id)
    if not current:
        raise NotFoundError("Ticket no encontrado")
    st = _norm_estado(current.get("estado"))
    if st == "en_proceso":
        return TicketRead(**_row_to_read(current))
    row = await _iniciar_transition(client_id, ticket_id, empresa_id=empresa_id)
    if row:
        return TicketRead(**_row_to_read(row))
    if st != "asignado":
        raise ValidationError("Solo se puede iniciar un ticket en estado asignado.")
    raise ValidationError(
        "No se pudo iniciar el ticket; intente nuevamente o verifique el estado."
    )


async def resolver_ticket(
    client_id: UUID,
    ticket_id: UUID,
    solucion: str,
    empresa_id: Optional[UUID] = None,
) -> TicketRead:
    current = await _get(client_id, ticket_id, empresa_id=empresa_id)
    if not current:
        raise NotFoundError("Ticket no encontrado")
    st = _norm_estado(current.get("estado"))
    if st == "resuelto":
        return TicketRead(**_row_to_read(current))
    now = datetime.utcnow()
    row = await _resolver_transition(
        client_id, ticket_id, now, solucion, empresa_id=empresa_id
    )
    if row:
        return TicketRead(**_row_to_read(row))
    if st != "en_proceso":
        raise ValidationError("Solo se puede resolver un ticket en estado en_proceso.")
    raise ValidationError(
        "No se pudo resolver el ticket; intente nuevamente o verifique el estado."
    )


async def cerrar_ticket(
    client_id: UUID, ticket_id: UUID, empresa_id: Optional[UUID] = None
) -> TicketRead:
    current = await _get(client_id, ticket_id, empresa_id=empresa_id)
    if not current:
        raise NotFoundError("Ticket no encontrado")
    st = _norm_estado(current.get("estado"))
    if st == "cerrado":
        return TicketRead(**_row_to_read(current))
    row = await _cerrar_transition(client_id, ticket_id, empresa_id=empresa_id)
    if row:
        return TicketRead(**_row_to_read(row))
    if st != "resuelto":
        raise ValidationError("Solo se puede cerrar un ticket en estado resuelto.")
    raise ValidationError(
        "No se pudo cerrar el ticket; intente nuevamente o verifique el estado."
    )
