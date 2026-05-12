"""
Endpoints FastAPI para sls_cotizacion.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi import status

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.sls.application.services import (
    list_cotizaciones,
    get_cotizacion_by_id,
    create_cotizacion,
    update_cotizacion,
    get_detalle_cotizacion,
    put_detalle_cotizacion,
    enviar_cotizacion,
    aceptar_cotizacion,
    rechazar_cotizacion,
    convertir_cotizacion_a_pedido,
)
from app.modules.sls.presentation.schemas import (
    CotizacionCreate,
    CotizacionUpdate,
    CotizacionRead,
    CotizacionDetalleCreate,
    CotizacionDetalleRead,
    CotizacionRechazarBody,
    CotizacionConvertirPedidoResponse,
)
from app.core.exceptions import NotFoundError

MODULE_CODE = "sls"
RESOURCE_CODE = "cotizacion"

router = APIRouter()


@router.get("", response_model=List[CotizacionRead], tags=["SLS - Cotizaciones"])
async def get_cotizaciones(
    empresa_id: Optional[UUID] = Query(None),
    cliente_venta_id: Optional[UUID] = Query(None),
    vendedor_usuario_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista cotizaciones del tenant."""
    return await list_cotizaciones(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        cliente_venta_id=cliente_venta_id,
        vendedor_usuario_id=vendedor_usuario_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )


@router.get("/{cotizacion_id}", response_model=CotizacionRead, tags=["SLS - Cotizaciones"])
async def get_cotizacion(
    cotizacion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Obtiene una cotizacion por id."""
    try:
        return await get_cotizacion_by_id(current_user.cliente_id, cotizacion_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=CotizacionRead, status_code=status.HTTP_201_CREATED, tags=["SLS - Cotizaciones"])
async def post_cotizacion(
    data: CotizacionCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Crea una cotizacion."""
    return await create_cotizacion(current_user.cliente_id, data)


@router.put("/{cotizacion_id}", response_model=CotizacionRead, tags=["SLS - Cotizaciones"])
async def put_cotizacion(
    cotizacion_id: UUID,
    data: CotizacionUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza una cotizacion."""
    try:
        return await update_cotizacion(current_user.cliente_id, cotizacion_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{cotizacion_id}/detalle", response_model=List[CotizacionDetalleRead], tags=["SLS - Cotizaciones"])
async def get_cotizacion_detalle(
    cotizacion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Obtiene el detalle (embebido) de una cotización."""
    return await get_detalle_cotizacion(current_user.cliente_id, cotizacion_id)


@router.put("/{cotizacion_id}/detalle", response_model=List[CotizacionDetalleRead], tags=["SLS - Cotizaciones"])
async def put_cotizacion_detalle(
    cotizacion_id: UUID,
    items: List[CotizacionDetalleCreate] = Body(...),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Reemplaza el detalle (embebido) de una cotización. Solo en borrador."""
    return await put_detalle_cotizacion(current_user.cliente_id, cotizacion_id, items)


@router.post("/{cotizacion_id}/enviar", response_model=CotizacionRead, tags=["SLS - Cotizaciones"])
async def post_enviar_cotizacion(
    cotizacion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    return await enviar_cotizacion(current_user.cliente_id, cotizacion_id)


@router.post("/{cotizacion_id}/aceptar", response_model=CotizacionRead, tags=["SLS - Cotizaciones"])
async def post_aceptar_cotizacion(
    cotizacion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    return await aceptar_cotizacion(current_user.cliente_id, cotizacion_id)


@router.post("/{cotizacion_id}/rechazar", response_model=CotizacionRead, tags=["SLS - Cotizaciones"])
async def post_rechazar_cotizacion(
    cotizacion_id: UUID,
    body: CotizacionRechazarBody = Body(default_factory=CotizacionRechazarBody),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    return await rechazar_cotizacion(current_user.cliente_id, cotizacion_id, motivo=body.motivo_rechazo or "")


@router.post(
    "/{cotizacion_id}/convertir-a-pedido",
    response_model=CotizacionConvertirPedidoResponse,
    tags=["SLS - Cotizaciones"],
)
async def post_convertir_a_pedido(
    cotizacion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    return await convertir_cotizacion_a_pedido(current_user.cliente_id, cotizacion_id)
