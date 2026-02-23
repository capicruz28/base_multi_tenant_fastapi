"""Endpoints tkt ticket."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.tkt.application.services import (
    list_ticket,
    get_ticket_by_id,
    create_ticket,
    update_ticket,
)
from app.modules.tkt.presentation.schemas import (
    TicketCreate,
    TicketUpdate,
    TicketRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[TicketRead])
async def get_tickets(
    empresa_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
    asignado_usuario_id: Optional[UUID] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("tkt.ticket.leer")),
):
    return await list_ticket(
        current_user.cliente_id,
        empresa_id=empresa_id,
        estado=estado,
        prioridad=prioridad,
        categoria=categoria,
        asignado_usuario_id=asignado_usuario_id,
        buscar=buscar,
    )


@router.get("/{ticket_id}", response_model=TicketRead)
async def get_ticket(
    ticket_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("tkt.ticket.leer")),
):
    try:
        return await get_ticket_by_id(current_user.cliente_id, ticket_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
async def post_ticket(
    data: TicketCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await create_ticket(current_user.cliente_id, data)


@router.put("/{ticket_id}", response_model=TicketRead)
async def put_ticket(
    ticket_id: UUID,
    data: TicketUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("tkt.ticket.actualizar")),
):
    try:
        return await update_ticket(current_user.cliente_id, ticket_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
