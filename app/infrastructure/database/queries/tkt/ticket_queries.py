"""Queries para tkt_ticket. Filtro tenant: cliente_id."""
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


async def get_ticket_by_id(client_id: UUID, ticket_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(TktTicketTable).where(
        and_(
            TktTicketTable.c.cliente_id == client_id,
            TktTicketTable.c.ticket_id == ticket_id,
        )
    )
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
    client_id: UUID, ticket_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("ticket_id", "cliente_id")
    }
    if not payload:
        return await get_ticket_by_id(client_id, ticket_id)
    stmt = update(TktTicketTable).where(
        and_(
            TktTicketTable.c.cliente_id == client_id,
            TktTicketTable.c.ticket_id == ticket_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_ticket_by_id(client_id, ticket_id)
