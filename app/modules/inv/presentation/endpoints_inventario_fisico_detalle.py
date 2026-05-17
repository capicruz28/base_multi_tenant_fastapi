"""Endpoints INV - Inventario Físico Detalle. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.inv.presentation.schemas import (
    InventarioFisicoDetalleCreate,
    InventarioFisicoDetalleUpdate,
    InventarioFisicoDetalleRead,
)
from app.modules.inv.application.services import inventario_fisico_detalle_service
from app.core.exceptions import NotFoundError

router = APIRouter()

MODULE_CODE = "inv"
RESOURCE_CODE = "inventario_fisico"


@router.get(
    "",
    response_model=list[InventarioFisicoDetalleRead],
    summary="Listar detalle de inventarios físicos",
)
async def listar_inventarios_fisicos_detalle(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    inventario_fisico_id: Optional[UUID] = Query(
        None, description="Filtrar por cabecera de inventario físico"
    ),
    producto_id: Optional[UUID] = Query(
        None, description="Filtrar por producto en el detalle"
    ),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(
        require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")
    ),
):
    client_id = current_user.cliente_id
    return await inventario_fisico_detalle_service.list_inventarios_fisicos_detalle_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        inventario_fisico_id=inventario_fisico_id,
        producto_id=producto_id,
    )


@router.get(
    "/{inventario_fisico_detalle_id}",
    response_model=InventarioFisicoDetalleRead,
    summary="Detalle línea de inventario físico",
)
async def detalle_inventario_fisico_detalle(
    inventario_fisico_detalle_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(
        require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")
    ),
):
    client_id = current_user.cliente_id
    try:
        return await inventario_fisico_detalle_service.get_inventario_fisico_detalle_servicio(
            client_id=client_id,
            inventario_fisico_detalle_id=inventario_fisico_detalle_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "",
    response_model=InventarioFisicoDetalleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear línea de inventario físico",
    deprecated=True,
)
async def crear_inventario_fisico_detalle(
    data: InventarioFisicoDetalleCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(
        require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")
    ),
):
    client_id = current_user.cliente_id
    return await inventario_fisico_detalle_service.create_inventario_fisico_detalle_servicio(
        client_id=client_id, data=data
    )


@router.put(
    "/{inventario_fisico_detalle_id}",
    response_model=InventarioFisicoDetalleRead,
    summary="Actualizar línea de inventario físico",
    deprecated=True,
)
async def actualizar_inventario_fisico_detalle(
    inventario_fisico_detalle_id: UUID,
    data: InventarioFisicoDetalleUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(
        require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")
    ),
):
    client_id = current_user.cliente_id
    try:
        return await inventario_fisico_detalle_service.update_inventario_fisico_detalle_servicio(
            client_id=client_id,
            inventario_fisico_detalle_id=inventario_fisico_detalle_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

