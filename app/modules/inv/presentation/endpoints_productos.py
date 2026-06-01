# app/modules/inv/presentation/endpoints_productos.py
"""Endpoints INV - Productos. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.core.exceptions import NotFoundError, AuthorizationError, ConflictError
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.inv.presentation.schemas import ProductoCreate, ProductoUpdate, ProductoRead
from app.modules.inv.application.services import producto_service

router = APIRouter()

MODULE_CODE = "inv"
RESOURCE_CODE = "producto"


@router.get("", response_model=list[ProductoRead], summary="Listar productos")
async def listar_productos(
    categoria_id: Optional[UUID] = Query(None, description="Filtrar por categoría"),
    tipo_producto: Optional[str] = Query(None, description="Filtrar por tipo de producto"),
    solo_activos: bool = Query(True, description="Solo productos activos"),
    buscar: Optional[str] = Query(None, description="Búsqueda por nombre, SKU o código de barras"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista productos de la empresa activa en sesión."""
    client_id = current_user.cliente_id
    return await producto_service.list_productos_servicio(
        client_id=client_id,
        categoria_id=categoria_id,
        tipo_producto=tipo_producto,
        solo_activos=solo_activos,
        buscar=buscar,
    )


@router.get("/{producto_id}", response_model=ProductoRead, summary="Detalle producto")
async def detalle_producto(
    producto_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Detalle de un producto de la empresa activa."""
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
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Crea un producto. empresa_id del body debe coincidir con la sesión."""
    client_id = current_user.cliente_id
    try:
        return await producto_service.create_producto_servicio(client_id=client_id, data=data)
    except AuthorizationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except ConflictError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.put("/{producto_id}", response_model=ProductoRead, summary="Actualizar producto")
async def actualizar_producto(
    producto_id: UUID,
    data: ProductoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza un producto de la empresa activa."""
    client_id = current_user.cliente_id
    try:
        return await producto_service.update_producto_servicio(
            client_id=client_id,
            producto_id=producto_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except ConflictError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.delete(
    "/{producto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar (baja lógica) producto",
)
async def eliminar_producto(
    producto_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.eliminar")),
):
    """Marca un producto como inactivo en la empresa activa."""
    client_id = current_user.cliente_id
    try:
        await producto_service.update_producto_servicio(
            client_id=client_id,
            producto_id=producto_id,
            data=ProductoUpdate(es_activo=False),
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "/{producto_id}/reactivar",
    response_model=ProductoRead,
    summary="Reactivar producto",
)
async def reactivar_producto(
    producto_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Reactiva un producto de la empresa activa."""
    client_id = current_user.cliente_id
    try:
        return await producto_service.update_producto_servicio(
            client_id=client_id,
            producto_id=producto_id,
            data=ProductoUpdate(es_activo=True),
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
