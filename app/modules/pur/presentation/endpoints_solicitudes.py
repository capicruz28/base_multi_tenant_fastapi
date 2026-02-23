# app/modules/pur/presentation/endpoints_solicitudes.py
"""Endpoints PUR - Solicitudes de Compra. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional
from datetime import date

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.pur.presentation.schemas import SolicitudCompraCreate, SolicitudCompraUpdate, SolicitudCompraRead
from app.modules.pur.application.services import solicitud_service
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=list[SolicitudCompraRead], summary="Listar solicitudes de compra")
async def listar_solicitudes(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    fecha_desde: Optional[date] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista solicitudes de compra del tenant. Filtro por cliente_id del token."""
    client_id = current_user.cliente_id
    return await solicitud_service.list_solicitudes_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )


@router.get("/{solicitud_id}", response_model=SolicitudCompraRead, summary="Detalle solicitud")
async def detalle_solicitud(
    solicitud_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Detalle de una solicitud. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await solicitud_service.get_solicitud_servicio(
            client_id=client_id,
            solicitud_id=solicitud_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=SolicitudCompraRead, status_code=status.HTTP_201_CREATED, summary="Crear solicitud")
async def crear_solicitud(
    data: SolicitudCompraCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea una solicitud de compra. cliente_id se asigna desde el contexto (tenant), no desde el body."""
    client_id = current_user.cliente_id
    return await solicitud_service.create_solicitud_servicio(client_id=client_id, data=data)


@router.put("/{solicitud_id}", response_model=SolicitudCompraRead, summary="Actualizar solicitud")
async def actualizar_solicitud(
    solicitud_id: UUID,
    data: SolicitudCompraUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza una solicitud. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await solicitud_service.update_solicitud_servicio(
            client_id=client_id,
            solicitud_id=solicitud_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
