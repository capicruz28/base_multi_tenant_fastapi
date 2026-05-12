"""Queries para tkt_ticket. Filtro tenant: cliente_id."""
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_
from app.infrastructure.database.tables_erp import TktTicketTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in TktTicketTable.c}


async def list_ticket(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    categoria: Optional[str] = None,
    asignado_usuario_id: Optional[UUID] = None,
    buscar: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = select(TktTicketTable).where(TktTicketTable.c.cliente_id == client_id)
    if empresa_id:
        q = q.where(TktTicketTable.c.empresa_id == empresa_id)
    if estado:
        q = q.where(TktTicketTable.c.estado == estado)
    if prioridad:
        q = q.where(TktTicketTable.c.prioridad == prioridad)
    if categoria:
        q = q.where(TktTicketTable.c.categoria == categoria)
    if asignado_usuario_id:
        q = q.where(TktTicketTable.c.asignado_usuario_id == asignado_usuario_id)
    if buscar:
        q = q.where(or_(
            TktTicketTable.c.numero_ticket.ilike(f"%{buscar}%"),
            TktTicketTable.c.asunto.ilike(f"%{buscar}%"),
            TktTicketTable.c.descripcion.ilike(f"%{buscar}%"),
        ))
    q = q.order_by(TktTicketTable.c.fecha_creacion.desc(), TktTicketTable.c.numero_ticket)
    return await execute_query(q, client_id=client_id)


async def get_ticket_by_id(
    client_id: UUID, ticket_id: UUID, empresa_id: Optional[UUID] = None
) -> Optional[Dict[str, Any]]:
    cond = [
        TktTicketTable.c.cliente_id == client_id,
        TktTicketTable.c.ticket_id == ticket_id,
    ]
    if empresa_id:
        cond.append(TktTicketTable.c.empresa_id == empresa_id)
    q = select(TktTicketTable).where(and_(*cond))
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_ticket(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("ticket_id", uuid4())
    await execute_insert(insert(TktTicketTable).values(**payload), client_id=client_id)
    return await get_ticket_by_id(client_id, payload["ticket_id"])


async def update_ticket(
    client_id: UUID,
    ticket_id: UUID,
    data: Dict[str, Any],
    empresa_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("ticket_id", "cliente_id")
    }
    if not payload:
        return await get_ticket_by_id(client_id, ticket_id, empresa_id=empresa_id)
    stmt = update(TktTicketTable).where(
        and_(
            TktTicketTable.c.cliente_id == client_id,
            TktTicketTable.c.ticket_id == ticket_id,
            *( [TktTicketTable.c.empresa_id == empresa_id] if empresa_id else [] ),
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_ticket_by_id(client_id, ticket_id, empresa_id=empresa_id)


async def assign_ticket_transition(
    client_id: UUID,
    ticket_id: UUID,
    asignado_usuario_id: UUID,
    fecha_asignacion: datetime,
    empresa_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    cond = [
        TktTicketTable.c.cliente_id == client_id,
        TktTicketTable.c.ticket_id == ticket_id,
        TktTicketTable.c.estado == "abierto",
    ]
    if empresa_id:
        cond.append(TktTicketTable.c.empresa_id == empresa_id)
    stmt = (
        update(TktTicketTable)
        .where(and_(*cond))
        .values(
            estado="asignado",
            asignado_usuario_id=asignado_usuario_id,
            fecha_asignacion=fecha_asignacion,
        )
    )
    res = await execute_update(stmt, client_id=client_id)
    if (res or {}).get("rows_affected", 0) <= 0:
        return None
    return await get_ticket_by_id(client_id, ticket_id, empresa_id=empresa_id)


async def iniciar_ticket_transition(
    client_id: UUID, ticket_id: UUID, empresa_id: Optional[UUID] = None
) -> Optional[Dict[str, Any]]:
    cond = [
        TktTicketTable.c.cliente_id == client_id,
        TktTicketTable.c.ticket_id == ticket_id,
        TktTicketTable.c.estado == "asignado",
    ]
    if empresa_id:
        cond.append(TktTicketTable.c.empresa_id == empresa_id)
    stmt = update(TktTicketTable).where(and_(*cond)).values(estado="en_proceso")
    res = await execute_update(stmt, client_id=client_id)
    if (res or {}).get("rows_affected", 0) <= 0:
        return None
    return await get_ticket_by_id(client_id, ticket_id, empresa_id=empresa_id)


async def resolver_ticket_transition(
    client_id: UUID,
    ticket_id: UUID,
    fecha_resolucion: datetime,
    solucion: str,
    empresa_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    cond = [
        TktTicketTable.c.cliente_id == client_id,
        TktTicketTable.c.ticket_id == ticket_id,
        TktTicketTable.c.estado == "en_proceso",
    ]
    if empresa_id:
        cond.append(TktTicketTable.c.empresa_id == empresa_id)
    stmt = (
        update(TktTicketTable)
        .where(and_(*cond))
        .values(estado="resuelto", fecha_resolucion=fecha_resolucion, solucion=solucion)
    )
    res = await execute_update(stmt, client_id=client_id)
    if (res or {}).get("rows_affected", 0) <= 0:
        return None
    return await get_ticket_by_id(client_id, ticket_id, empresa_id=empresa_id)


async def cerrar_ticket_transition(
    client_id: UUID, ticket_id: UUID, empresa_id: Optional[UUID] = None
) -> Optional[Dict[str, Any]]:
    cond = [
        TktTicketTable.c.cliente_id == client_id,
        TktTicketTable.c.ticket_id == ticket_id,
        TktTicketTable.c.estado == "resuelto",
    ]
    if empresa_id:
        cond.append(TktTicketTable.c.empresa_id == empresa_id)
    stmt = update(TktTicketTable).where(and_(*cond)).values(estado="cerrado")
    res = await execute_update(stmt, client_id=client_id)
    if (res or {}).get("rows_affected", 0) <= 0:
        return None
    return await get_ticket_by_id(client_id, ticket_id, empresa_id=empresa_id)
