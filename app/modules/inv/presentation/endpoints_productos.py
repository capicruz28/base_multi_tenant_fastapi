# app/modules/inv/presentation/endpoints_productos.py
"""Endpoints INV - Productos. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.inv.presentation.schemas import ProductoCreate, ProductoUpdate, ProductoRead
from app.modules.inv.application.services import producto_service
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=list[ProductoRead], summary="Listar productos")
async def listar_productos(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    categoria_id: Optional[UUID] = Query(None, description="Filtrar por categoría"),
    tipo_producto: Optional[str] = Query(None, description="Filtrar por tipo de producto"),
    solo_activos: bool = Query(True, description="Solo productos activos"),
    buscar: Optional[str] = Query(None, description="Búsqueda por nombre, SKU o código de barras"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista productos del tenant. Filtro por cliente_id del token."""
    client_id = current_user.cliente_id
    return await producto_service.list_productos_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        categoria_id=categoria_id,
        tipo_producto=tipo_producto,
        solo_activos=solo_activos,
        buscar=buscar,
    )


@router.get("/{producto_id}", response_model=ProductoRead, summary="Detalle producto")
async def detalle_producto(
    producto_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Detalle de un producto. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await producto_service.get_producto_servicio(
            client_id=client_id,
            producto_id=producto_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=ProductoRead, status_code=status.HTTP_201_CREATED, summary="Crear producto")
async def crear_producto(
    data: ProductoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un producto. cliente_id se asigna desde el contexto (tenant), no desde el body."""
    client_id = current_user.cliente_id
    return await producto_service.create_producto_servicio(client_id=client_id, data=data)


@router.put("/{producto_id}", response_model=ProductoRead, summary="Actualizar producto")
async def actualizar_producto(
    producto_id: UUID,
    data: ProductoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un producto. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await producto_service.update_producto_servicio(
            client_id=client_id,
            producto_id=producto_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
