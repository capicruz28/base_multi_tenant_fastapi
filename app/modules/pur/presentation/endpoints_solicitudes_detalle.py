"""Endpoints PUR - Solicitudes de Compra Detalle. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.pur.presentation.schemas import (
    SolicitudCompraDetalleCreate,
    SolicitudCompraDetalleUpdate,
    SolicitudCompraDetalleRead,
)
from app.modules.pur.application.services import solicitud_detalle_service
from app.core.exceptions import NotFoundError

MODULE_CODE = "pur"
RESOURCE_CODE = "solicitud"

router = APIRouter()


@router.get(
    "",
    response_model=list[SolicitudCompraDetalleRead],
    summary="Listar detalle de solicitudes de compra",
)
async def listar_solicitudes_detalle(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    solicitud_id: Optional[UUID] = Query(
        None, description="Filtrar por cabecera de solicitud de compra"
    ),
    producto_id: Optional[UUID] = Query(
        None, description="Filtrar por producto en el detalle"
    ),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista líneas de solicitudes de compra del tenant. Filtro por cliente_id del token."""
    client_id = current_user.cliente_id
    return await solicitud_detalle_service.list_solicitudes_detalle_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        solicitud_id=solicitud_id,
        producto_id=producto_id,
    )


@router.get(
    "/{solicitud_detalle_id}",
    response_model=SolicitudCompraDetalleRead,
    summary="Detalle línea de solicitud de compra",
)
async def detalle_solicitud_detalle(
    solicitud_detalle_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Detalle de una línea de solicitud de compra. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await solicitud_detalle_service.get_solicitud_detalle_servicio(
            client_id=client_id,
            solicitud_detalle_id=solicitud_detalle_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "",
    response_model=SolicitudCompraDetalleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear línea de solicitud de compra",
)
async def crear_solicitud_detalle(
    data: SolicitudCompraDetalleCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Crea una línea de solicitud de compra. cliente_id se asigna desde el contexto (tenant), no desde el body."""
    client_id = current_user.cliente_id
    return await solicitud_detalle_service.create_solicitud_detalle_servicio(
        client_id=client_id,
        data=data,
    )


@router.put(
    "/{solicitud_detalle_id}",
    response_model=SolicitudCompraDetalleRead,
    summary="Actualizar línea de solicitud de compra",
)
async def actualizar_solicitud_detalle(
    solicitud_detalle_id: UUID,
    data: SolicitudCompraDetalleUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza una línea de solicitud de compra. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await solicitud_detalle_service.update_solicitud_detalle_servicio(
            client_id=client_id,
            solicitud_detalle_id=solicitud_detalle_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


