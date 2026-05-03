"""Endpoints PUR - Cotizaciones Detalle. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.pur.presentation.schemas import (
    CotizacionDetalleCreate,
    CotizacionDetalleUpdate,
    CotizacionDetalleRead,
)
from app.modules.pur.application.services import cotizacion_detalle_service
from app.core.exceptions import NotFoundError

MODULE_CODE = "pur"
RESOURCE_CODE = "cotizacion"

router = APIRouter()


@router.get(
    "",
    response_model=list[CotizacionDetalleRead],
    summary="Listar detalle de cotizaciones",
)
async def listar_cotizaciones_detalle(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    cotizacion_id: Optional[UUID] = Query(
        None, description="Filtrar por cabecera de cotización"
    ),
    producto_id: Optional[UUID] = Query(
        None, description="Filtrar por producto en el detalle"
    ),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista líneas de cotizaciones del tenant. Filtro por cliente_id del token."""
    client_id = current_user.cliente_id
    return await cotizacion_detalle_service.list_cotizaciones_detalle_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        cotizacion_id=cotizacion_id,
        producto_id=producto_id,
    )


@router.get(
    "/{cotizacion_detalle_id}",
    response_model=CotizacionDetalleRead,
    summary="Detalle línea de cotización",
)
async def detalle_cotizacion_detalle(
    cotizacion_detalle_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Detalle de una línea de cotización. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await cotizacion_detalle_service.get_cotizacion_detalle_servicio(
            client_id=client_id,
            cotizacion_detalle_id=cotizacion_detalle_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "",
    response_model=CotizacionDetalleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear línea de cotización",
)
async def crear_cotizacion_detalle(
    data: CotizacionDetalleCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Crea una línea de cotización. cliente_id se asigna desde el contexto (tenant), no desde el body."""
    client_id = current_user.cliente_id
    return await cotizacion_detalle_service.create_cotizacion_detalle_servicio(
        client_id=client_id,
        data=data,
    )


@router.put(
    "/{cotizacion_detalle_id}",
    response_model=CotizacionDetalleRead,
    summary="Actualizar línea de cotización",
)
async def actualizar_cotizacion_detalle(
    cotizacion_detalle_id: UUID,
    data: CotizacionDetalleUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza una línea de cotización. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await cotizacion_detalle_service.update_cotizacion_detalle_servicio(
            client_id=client_id,
            cotizacion_detalle_id=cotizacion_detalle_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


