# app/modules/pur/presentation/endpoints_cotizaciones.py
"""Endpoints PUR - Cotizaciones. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional
from datetime import date

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.pur.presentation.schemas import CotizacionCreate, CotizacionUpdate, CotizacionRead
from app.modules.pur.application.services import cotizacion_service
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=list[CotizacionRead], summary="Listar cotizaciones")
async def listar_cotizaciones(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    proveedor_id: Optional[UUID] = Query(None, description="Filtrar por proveedor"),
    solicitud_compra_id: Optional[UUID] = Query(None, description="Filtrar por solicitud"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    fecha_desde: Optional[date] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista cotizaciones del tenant. Filtro por cliente_id del token."""
    client_id = current_user.cliente_id
    return await cotizacion_service.list_cotizaciones_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        proveedor_id=proveedor_id,
        solicitud_compra_id=solicitud_compra_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )


@router.get("/{cotizacion_id}", response_model=CotizacionRead, summary="Detalle cotización")
async def detalle_cotizacion(
    cotizacion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
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


@router.post("", response_model=CotizacionRead, status_code=status.HTTP_201_CREATED, summary="Crear cotización")
async def crear_cotizacion(
    data: CotizacionCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea una cotización. cliente_id se asigna desde el contexto (tenant), no desde el body."""
    client_id = current_user.cliente_id
    return await cotizacion_service.create_cotizacion_servicio(client_id=client_id, data=data)


@router.put("/{cotizacion_id}", response_model=CotizacionRead, summary="Actualizar cotización")
async def actualizar_cotizacion(
    cotizacion_id: UUID,
    data: CotizacionUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
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
