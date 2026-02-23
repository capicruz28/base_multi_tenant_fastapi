# app/modules/inv/presentation/endpoints_inventario_fisico.py
"""Endpoints INV - Inventario Físico. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional
from datetime import date

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.inv.presentation.schemas import InventarioFisicoCreate, InventarioFisicoUpdate, InventarioFisicoRead
from app.modules.inv.application.services import inventario_fisico_service
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=list[InventarioFisicoRead], summary="Listar inventarios físicos")
async def listar_inventarios_fisicos(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    almacen_id: Optional[UUID] = Query(None, description="Filtrar por almacén"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    fecha_desde: Optional[date] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista inventarios físicos del tenant. Filtro por cliente_id del token."""
    client_id = current_user.cliente_id
    return await inventario_fisico_service.list_inventarios_fisicos_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        almacen_id=almacen_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )


@router.get("/{inventario_fisico_id}", response_model=InventarioFisicoRead, summary="Detalle inventario físico")
async def detalle_inventario_fisico(
    inventario_fisico_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Detalle de un inventario físico. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await inventario_fisico_service.get_inventario_fisico_servicio(
            client_id=client_id,
            inventario_fisico_id=inventario_fisico_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=InventarioFisicoRead, status_code=status.HTTP_201_CREATED, summary="Crear inventario físico")
async def crear_inventario_fisico(
    data: InventarioFisicoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un inventario físico. cliente_id se asigna desde el contexto (tenant), no desde el body."""
    client_id = current_user.cliente_id
    return await inventario_fisico_service.create_inventario_fisico_servicio(client_id=client_id, data=data)


@router.put("/{inventario_fisico_id}", response_model=InventarioFisicoRead, summary="Actualizar inventario físico")
async def actualizar_inventario_fisico(
    inventario_fisico_id: UUID,
    data: InventarioFisicoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un inventario físico. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await inventario_fisico_service.update_inventario_fisico_servicio(
            client_id=client_id,
            inventario_fisico_id=inventario_fisico_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
