"""Endpoints cst producto costo."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.cst.application.services import (
    list_producto_costo,
    get_producto_costo_by_id,
    create_producto_costo,
    update_producto_costo,
)
from app.modules.cst.presentation.schemas import (
    ProductoCostoCreate,
    ProductoCostoUpdate,
    ProductoCostoRead,
)
from app.core.exceptions import NotFoundError

MODULE_CODE = "cst"
RESOURCE_CODE = "producto_costo"

router = APIRouter()


@router.get("", response_model=List[ProductoCostoRead])
async def get_productos_costo(
    empresa_id: Optional[UUID] = Query(None),
    producto_id: Optional[UUID] = Query(None),
    anio: Optional[int] = Query(None, ge=2000, le=2100),
    mes: Optional[int] = Query(None, ge=1, le=12),
    metodo_costeo: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    return await list_producto_costo(
        current_user.cliente_id,
        empresa_id=empresa_id,
        producto_id=producto_id,
        anio=anio,
        mes=mes,
        metodo_costeo=metodo_costeo,
    )


@router.get("/{producto_costo_id}", response_model=ProductoCostoRead)
async def get_producto_costo(
    producto_costo_id: UUID,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    try:
        return await get_producto_costo_by_id(
            current_user.cliente_id, producto_costo_id, empresa_id=empresa_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=ProductoCostoRead, status_code=status.HTTP_201_CREATED)
async def post_producto_costo(
    data: ProductoCostoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    return await create_producto_costo(current_user.cliente_id, data)


@router.put("/{producto_costo_id}", response_model=ProductoCostoRead)
async def put_producto_costo(
    producto_costo_id: UUID,
    data: ProductoCostoUpdate,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    try:
        return await update_producto_costo(
            current_user.cliente_id, producto_costo_id, data, empresa_id=empresa_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
