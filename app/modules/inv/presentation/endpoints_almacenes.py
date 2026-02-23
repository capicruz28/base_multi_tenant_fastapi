# app/modules/inv/presentation/endpoints_almacenes.py
"""Endpoints INV - Almacenes. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.inv.presentation.schemas import AlmacenCreate, AlmacenUpdate, AlmacenRead
from app.modules.inv.application.services import almacen_service
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=list[AlmacenRead], summary="Listar almacenes")
async def listar_almacenes(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    sucursal_id: Optional[UUID] = Query(None, description="Filtrar por sucursal"),
    solo_activos: bool = Query(True, description="Solo almacenes activos"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista almacenes del tenant. Filtro por cliente_id del token."""
    client_id = current_user.cliente_id
    return await almacen_service.list_almacenes_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        sucursal_id=sucursal_id,
        solo_activos=solo_activos,
    )


@router.get("/{almacen_id}", response_model=AlmacenRead, summary="Detalle almacén")
async def detalle_almacen(
    almacen_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Detalle de un almacén. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await almacen_service.get_almacen_servicio(
            client_id=client_id,
            almacen_id=almacen_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=AlmacenRead, status_code=status.HTTP_201_CREATED, summary="Crear almacén")
async def crear_almacen(
    data: AlmacenCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un almacén. cliente_id se asigna desde el contexto (tenant), no desde el body."""
    client_id = current_user.cliente_id
    return await almacen_service.create_almacen_servicio(client_id=client_id, data=data)


@router.put("/{almacen_id}", response_model=AlmacenRead, summary="Actualizar almacén")
async def actualizar_almacen(
    almacen_id: UUID,
    data: AlmacenUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un almacén. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await almacen_service.update_almacen_servicio(
            client_id=client_id,
            almacen_id=almacen_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
