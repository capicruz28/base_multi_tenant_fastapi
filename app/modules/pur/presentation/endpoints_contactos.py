# app/modules/pur/presentation/endpoints_contactos.py
"""Endpoints PUR - Contactos de Proveedor. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.pur.presentation.schemas import ContactoProveedorCreate, ContactoProveedorUpdate, ContactoProveedorRead
from app.modules.pur.application.services import contacto_service
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=list[ContactoProveedorRead], summary="Listar contactos")
async def listar_contactos(
    proveedor_id: Optional[UUID] = Query(None, description="Filtrar por proveedor"),
    solo_activos: bool = Query(True, description="Solo contactos activos"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista contactos del tenant. Filtro por cliente_id del token."""
    client_id = current_user.cliente_id
    return await contacto_service.list_contactos_servicio(
        client_id=client_id,
        proveedor_id=proveedor_id,
        solo_activos=solo_activos,
    )


@router.get("/{contacto_id}", response_model=ContactoProveedorRead, summary="Detalle contacto")
async def detalle_contacto(
    contacto_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Detalle de un contacto. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await contacto_service.get_contacto_servicio(
            client_id=client_id,
            contacto_id=contacto_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=ContactoProveedorRead, status_code=status.HTTP_201_CREATED, summary="Crear contacto")
async def crear_contacto(
    data: ContactoProveedorCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un contacto. cliente_id se asigna desde el contexto (tenant), no desde el body."""
    client_id = current_user.cliente_id
    return await contacto_service.create_contacto_servicio(client_id=client_id, data=data)


@router.put("/{contacto_id}", response_model=ContactoProveedorRead, summary="Actualizar contacto")
async def actualizar_contacto(
    contacto_id: UUID,
    data: ContactoProveedorUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un contacto. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await contacto_service.update_contacto_servicio(
            client_id=client_id,
            contacto_id=contacto_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
