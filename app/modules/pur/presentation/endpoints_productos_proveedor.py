# app/modules/pur/presentation/endpoints_productos_proveedor.py
"""Endpoints PUR - Productos por Proveedor. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.pur.presentation.schemas import ProductoProveedorCreate, ProductoProveedorUpdate, ProductoProveedorRead
from app.modules.pur.application.services import producto_proveedor_service
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=list[ProductoProveedorRead], summary="Listar productos por proveedor")
async def listar_productos_proveedor(
    proveedor_id: Optional[UUID] = Query(None, description="Filtrar por proveedor"),
    producto_id: Optional[UUID] = Query(None, description="Filtrar por producto"),
    solo_activos: bool = Query(True, description="Solo productos activos"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista productos por proveedor del tenant. Filtro por cliente_id del token."""
    client_id = current_user.cliente_id
    return await producto_proveedor_service.list_productos_proveedor_servicio(
        client_id=client_id,
        proveedor_id=proveedor_id,
        producto_id=producto_id,
        solo_activos=solo_activos,
    )


@router.get("/{producto_proveedor_id}", response_model=ProductoProveedorRead, summary="Detalle producto por proveedor")
async def detalle_producto_proveedor(
    producto_proveedor_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Detalle de un producto por proveedor. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await producto_proveedor_service.get_producto_proveedor_servicio(
            client_id=client_id,
            producto_proveedor_id=producto_proveedor_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=ProductoProveedorRead, status_code=status.HTTP_201_CREATED, summary="Crear producto por proveedor")
async def crear_producto_proveedor(
    data: ProductoProveedorCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un producto por proveedor. cliente_id se asigna desde el contexto (tenant), no desde el body."""
    client_id = current_user.cliente_id
    return await producto_proveedor_service.create_producto_proveedor_servicio(client_id=client_id, data=data)


@router.put("/{producto_proveedor_id}", response_model=ProductoProveedorRead, summary="Actualizar producto por proveedor")
async def actualizar_producto_proveedor(
    producto_proveedor_id: UUID,
    data: ProductoProveedorUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un producto por proveedor. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await producto_proveedor_service.update_producto_proveedor_servicio(
            client_id=client_id,
            producto_proveedor_id=producto_proveedor_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
