# app/modules/pur/presentation/endpoints_ordenes_compra.py
"""Endpoints PUR - Órdenes de Compra. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional
from datetime import date

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.pur.presentation.schemas import OrdenCompraCreate, OrdenCompraUpdate, OrdenCompraRead
from app.modules.pur.application.services import orden_compra_service
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=list[OrdenCompraRead], summary="Listar órdenes de compra")
async def listar_ordenes_compra(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    proveedor_id: Optional[UUID] = Query(None, description="Filtrar por proveedor"),
    solicitud_compra_id: Optional[UUID] = Query(None, description="Filtrar por solicitud"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    fecha_desde: Optional[date] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista órdenes de compra del tenant. Filtro por cliente_id del token."""
    client_id = current_user.cliente_id
    return await orden_compra_service.list_ordenes_compra_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        proveedor_id=proveedor_id,
        solicitud_compra_id=solicitud_compra_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )


@router.get("/{orden_compra_id}", response_model=OrdenCompraRead, summary="Detalle orden de compra")
async def detalle_orden_compra(
    orden_compra_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Detalle de una orden de compra. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await orden_compra_service.get_orden_compra_servicio(
            client_id=client_id,
            orden_compra_id=orden_compra_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=OrdenCompraRead, status_code=status.HTTP_201_CREATED, summary="Crear orden de compra")
async def crear_orden_compra(
    data: OrdenCompraCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea una orden de compra. cliente_id se asigna desde el contexto (tenant), no desde el body."""
    client_id = current_user.cliente_id
    return await orden_compra_service.create_orden_compra_servicio(client_id=client_id, data=data)


@router.put("/{orden_compra_id}", response_model=OrdenCompraRead, summary="Actualizar orden de compra")
async def actualizar_orden_compra(
    orden_compra_id: UUID,
    data: OrdenCompraUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza una orden de compra. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await orden_compra_service.update_orden_compra_servicio(
            client_id=client_id,
            orden_compra_id=orden_compra_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
