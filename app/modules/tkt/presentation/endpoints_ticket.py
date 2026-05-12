"""Endpoints tkt ticket."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.tkt.application.services import (
    list_ticket,
    get_ticket_by_id,
    create_ticket,
    update_ticket,
    assign_ticket,
    iniciar_ticket,
    resolver_ticket,
    cerrar_ticket,
)
from app.modules.tkt.presentation.schemas import (
    TicketCreate,
    TicketUpdate,
    TicketRead,
)
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter()


class TicketAsignarBody(BaseModel):
    asignado_usuario_id: UUID = Field(..., description="Usuario asignado al ticket")


class TicketResolverBody(BaseModel):
    solucion: str = Field(..., min_length=1, description="Solución del ticket")


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
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("tkt.ticket.leer")),
):
    try:
        return await get_ticket_by_id(
            current_user.cliente_id, ticket_id, empresa_id=empresa_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
async def post_ticket(
    data: TicketCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("tkt.ticket.crear")),
):
    return await create_ticket(current_user.cliente_id, data)


@router.put("/{ticket_id}", response_model=TicketRead)
async def put_ticket(
    ticket_id: UUID,
    data: TicketUpdate,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("tkt.ticket.actualizar")),
):
    try:
        return await update_ticket(
            current_user.cliente_id, ticket_id, data, empresa_id=empresa_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/{ticket_id}/asignar", response_model=TicketRead)
async def post_ticket_asignar(
    ticket_id: UUID,
    body: TicketAsignarBody,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("tkt.ticket.asignar")),
):
    try:
        return await assign_ticket(
            current_user.cliente_id,
            ticket_id,
            body.asignado_usuario_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/{ticket_id}/iniciar", response_model=TicketRead)
async def post_ticket_iniciar(
    ticket_id: UUID,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("tkt.ticket.actualizar")),
):
    try:
        return await iniciar_ticket(
            current_user.cliente_id, ticket_id, empresa_id=empresa_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/{ticket_id}/resolver", response_model=TicketRead)
async def post_ticket_resolver(
    ticket_id: UUID,
    body: TicketResolverBody,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("tkt.ticket.resolver")),
):
    try:
        return await resolver_ticket(
            current_user.cliente_id,
            ticket_id,
            body.solucion,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/{ticket_id}/cerrar", response_model=TicketRead)
async def post_ticket_cerrar(
    ticket_id: UUID,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("tkt.ticket.cerrar")),
):
    try:
        return await cerrar_ticket(
            current_user.cliente_id, ticket_id, empresa_id=empresa_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
