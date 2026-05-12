# app/modules/pur/presentation/endpoints_cotizaciones.py
"""Endpoints PUR - Cotizaciones. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from uuid import UUID
from typing import Optional
from datetime import date

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.pur.presentation.schemas import (
    CotizacionCreate,
    CotizacionUpdate,
    CotizacionRead,
    PurMotivoRechazoBody,
)
from app.modules.pur.application.services import cotizacion_service
from app.core.exceptions import NotFoundError

MODULE_CODE = "pur"
RESOURCE_CODE = "cotizacion"

router = APIRouter()


@router.get("", response_model=list[CotizacionRead], summary="Listar cotizaciones")
async def listar_cotizaciones(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    proveedor_id: Optional[UUID] = Query(None, description="Filtrar por proveedor"),
    solicitud_compra_id: Optional[UUID] = Query(None, description="Filtrar por solicitud"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    fecha_desde: Optional[date] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta"),
    page: Optional[int] = Query(None, ge=1, description="Página (con page_size)"),
    page_size: Optional[int] = Query(None, ge=1, le=500, description="Registros por página"),
    sort_by: Optional[str] = Query(None, description="Ordenar por: fecha_cotizacion, estado, fecha_creacion"),
    order: Optional[str] = Query(None, description="asc o desc"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista cotizaciones del tenant. Paginación opcional con page y page_size."""
    client_id = current_user.cliente_id
    return await cotizacion_service.list_cotizaciones_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        proveedor_id=proveedor_id,
        solicitud_compra_id=solicitud_compra_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        order=order,
    )


@router.post("", response_model=CotizacionRead, status_code=status.HTTP_201_CREATED, summary="Crear cotización")
async def crear_cotizacion(
    data: CotizacionCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Crea una cotización. cliente_id se asigna desde el contexto (tenant), no desde el body."""
    client_id = current_user.cliente_id
    return await cotizacion_service.create_cotizacion_servicio(client_id=client_id, data=data)


@router.put("/{cotizacion_id}", response_model=CotizacionRead, summary="Actualizar cotización")
async def actualizar_cotizacion(
    cotizacion_id: UUID,
    data: CotizacionUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza una cotización. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await cotizacion_service.update_cotizacion_servicio(
            client_id=client_id,
            cotizacion_id=cotizacion_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{cotizacion_id}/aceptar", response_model=CotizacionRead, summary="Aceptar cotización")
async def aceptar_cotizacion(
    cotizacion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Pasa la cotización a estado aceptada (desde pendiente, recibida o evaluada)."""
    client_id = current_user.cliente_id
    try:
        return await cotizacion_service.aceptar_cotizacion_servicio(
            client_id=client_id,
            cotizacion_id=cotizacion_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{cotizacion_id}/rechazar", response_model=CotizacionRead, summary="Rechazar cotización")
async def rechazar_cotizacion(
    cotizacion_id: UUID,
    body: Optional[PurMotivoRechazoBody] = Body(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Pasa la cotización a estado rechazada. Body opcional: motivo_rechazo."""
    client_id = current_user.cliente_id
    body_data = body or PurMotivoRechazoBody()
    try:
        return await cotizacion_service.rechazar_cotizacion_servicio(
            client_id=client_id,
            cotizacion_id=cotizacion_id,
            motivo_rechazo=body_data.motivo_rechazo or None,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{cotizacion_id}/marcar-ganadora", response_model=CotizacionRead, summary="Marcar cotización ganadora")
async def marcar_ganadora_cotizacion(
    cotizacion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Marca esta cotización como ganadora. Otras cotizaciones de la misma solicitud quedan no ganadoras."""
    client_id = current_user.cliente_id
    try:
        return await cotizacion_service.marcar_ganadora_cotizacion_servicio(
            client_id=client_id,
            cotizacion_id=cotizacion_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/{cotizacion_id}", response_model=CotizacionRead, summary="Detalle cotización")
async def detalle_cotizacion(
    cotizacion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Detalle de una cotización. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await cotizacion_service.get_cotizacion_servicio(
            client_id=client_id,
            cotizacion_id=cotizacion_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
