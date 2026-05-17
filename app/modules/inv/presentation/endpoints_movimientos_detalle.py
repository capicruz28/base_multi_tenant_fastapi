"""Endpoints INV - Movimiento Detalle. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.inv.presentation.schemas import (
    MovimientoDetalleCreate,
    MovimientoDetalleUpdate,
    MovimientoDetalleRead,
)
from app.modules.inv.application.services import movimiento_detalle_service
from app.core.exceptions import NotFoundError

router = APIRouter()

MODULE_CODE = "inv"
RESOURCE_CODE = "movimiento"


@router.get(
    "",
    response_model=list[MovimientoDetalleRead],
    summary="Listar detalle de movimientos",
)
async def listar_movimientos_detalle(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    movimiento_id: Optional[UUID] = Query(
        None, description="Filtrar por cabecera de movimiento"
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
    return await movimiento_detalle_service.list_movimientos_detalle_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        movimiento_id=movimiento_id,
        producto_id=producto_id,
    )


@router.get(
    "/{movimiento_detalle_id}",
    response_model=MovimientoDetalleRead,
    summary="Detalle línea de movimiento",
)
async def detalle_movimiento_detalle(
    movimiento_detalle_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(
        require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")
    ),
):
    client_id = current_user.cliente_id
    try:
        return await movimiento_detalle_service.get_movimiento_detalle_servicio(
            client_id=client_id,
            movimiento_detalle_id=movimiento_detalle_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "",
    response_model=MovimientoDetalleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear línea de movimiento",
    deprecated=True,
)
async def crear_movimiento_detalle(
    data: MovimientoDetalleCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(
        require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")
    ),
):
    client_id = current_user.cliente_id
    return await movimiento_detalle_service.create_movimiento_detalle_servicio(
        client_id=client_id, data=data
    )


@router.put(
    "/{movimiento_detalle_id}",
    response_model=MovimientoDetalleRead,
    summary="Actualizar línea de movimiento",
    deprecated=True,
)
async def actualizar_movimiento_detalle(
    movimiento_detalle_id: UUID,
    data: MovimientoDetalleUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(
        require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")
    ),
):
    client_id = current_user.cliente_id
    try:
        return await movimiento_detalle_service.update_movimiento_detalle_servicio(
            client_id=client_id,
            movimiento_detalle_id=movimiento_detalle_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

