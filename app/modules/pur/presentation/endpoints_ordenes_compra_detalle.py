"""Endpoints PUR - Órdenes de Compra Detalle. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.pur.presentation.schemas import (
    OrdenCompraDetalleCreate,
    OrdenCompraDetalleUpdate,
    OrdenCompraDetalleRead,
)
from app.modules.pur.application.services import orden_compra_detalle_service
from app.core.exceptions import NotFoundError

MODULE_CODE = "pur"
RESOURCE_CODE = "orden_compra"

router = APIRouter()


@router.get(
    "",
    response_model=list[OrdenCompraDetalleRead],
    summary="Listar detalle de órdenes de compra",
)
async def listar_ordenes_compra_detalle(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    orden_compra_id: Optional[UUID] = Query(
        None, description="Filtrar por cabecera de orden de compra"
    ),
    producto_id: Optional[UUID] = Query(
        None, description="Filtrar por producto en el detalle"
    ),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista líneas de órdenes de compra del tenant. Filtro por cliente_id del token."""
    client_id = current_user.cliente_id
    return await orden_compra_detalle_service.list_ordenes_compra_detalle_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        orden_compra_id=orden_compra_id,
        producto_id=producto_id,
    )


@router.get(
    "/{orden_compra_detalle_id}",
    response_model=OrdenCompraDetalleRead,
    summary="Detalle línea de orden de compra",
)
async def detalle_orden_compra_detalle(
    orden_compra_detalle_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Detalle de una línea de orden de compra. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await orden_compra_detalle_service.get_orden_compra_detalle_servicio(
            client_id=client_id,
            orden_compra_detalle_id=orden_compra_detalle_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "",
    response_model=OrdenCompraDetalleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear línea de orden de compra",
)
async def crear_orden_compra_detalle(
    data: OrdenCompraDetalleCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Crea una línea de orden de compra. cliente_id se asigna desde el contexto (tenant)."""
    client_id = current_user.cliente_id
    return await orden_compra_detalle_service.create_orden_compra_detalle_servicio(
        client_id=client_id,
        data=data,
    )


@router.put(
    "/{orden_compra_detalle_id}",
    response_model=OrdenCompraDetalleRead,
    summary="Actualizar línea de orden de compra",
)
async def actualizar_orden_compra_detalle(
    orden_compra_detalle_id: UUID,
    data: OrdenCompraDetalleUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza una línea de orden de compra. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await orden_compra_detalle_service.update_orden_compra_detalle_servicio(
            client_id=client_id,
            orden_compra_detalle_id=orden_compra_detalle_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
