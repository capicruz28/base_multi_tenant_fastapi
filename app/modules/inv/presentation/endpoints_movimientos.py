# app/modules/inv/presentation/endpoints_movimientos.py
"""Endpoints INV - Movimientos. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional
from datetime import date

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.inv.presentation.schemas import (
    MovimientoCreate,
    MovimientoUpdate,
    MovimientoRead,
    MovimientoConDetalleCreate,
    MovimientoConDetalleUpdate,
    MovimientoConDetalleRead,
)
from app.modules.inv.application.services import movimiento_service
from app.core.exceptions import NotFoundError

router = APIRouter()

MODULE_CODE = "inv"
RESOURCE_CODE = "movimiento"


@router.get("", response_model=list[MovimientoRead], summary="Listar movimientos")
async def listar_movimientos(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    tipo_movimiento_id: Optional[UUID] = Query(None, description="Filtrar por tipo de movimiento"),
    almacen_id: Optional[UUID] = Query(None, description="Filtrar por almacén"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    fecha_desde: Optional[date] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista movimientos del tenant. Filtro por cliente_id del token."""
    client_id = current_user.cliente_id
    return await movimiento_service.list_movimientos_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        tipo_movimiento_id=tipo_movimiento_id,
        almacen_id=almacen_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )


@router.get("/{movimiento_id}", response_model=MovimientoRead, summary="Detalle movimiento")
async def detalle_movimiento(
    movimiento_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Detalle de un movimiento. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await movimiento_service.get_movimiento_servicio(
            client_id=client_id,
            movimiento_id=movimiento_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=MovimientoRead, status_code=status.HTTP_201_CREATED, summary="Crear movimiento")
async def crear_movimiento(
    data: MovimientoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Crea un movimiento. cliente_id se asigna desde el contexto (tenant), no desde el body."""
    client_id = current_user.cliente_id
    return await movimiento_service.create_movimiento_servicio(client_id=client_id, data=data)


@router.put("/{movimiento_id}", response_model=MovimientoRead, summary="Actualizar movimiento")
async def actualizar_movimiento(
    movimiento_id: UUID,
    data: MovimientoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza un movimiento. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await movimiento_service.update_movimiento_servicio(
            client_id=client_id,
            movimiento_id=movimiento_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


# ============================================================================
# ENDPOINTS CABECERA + DETALLE EMBEBIDO
# ============================================================================

@router.get(
    "/{movimiento_id}/con-detalle",
    response_model=MovimientoConDetalleRead,
    summary="Detalle de movimiento con líneas embebidas",
)
async def detalle_movimiento_con_detalles(
    movimiento_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Retorna la cabecera del movimiento con todas sus líneas de detalle embebidas."""
    client_id = current_user.cliente_id
    try:
        return await movimiento_service.get_movimiento_con_detalles_servicio(
            client_id=client_id,
            movimiento_id=movimiento_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "/con-detalle",
    response_model=MovimientoConDetalleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear movimiento con líneas embebidas (recomendado)",
)
async def crear_movimiento_con_detalles(
    data: MovimientoConDetalleCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """
    Crea un movimiento con sus líneas de detalle en una sola transacción atómica.
    Requiere mínimo 1 línea. Calcula total_items/total_cantidad/total_costo automáticamente.
    """
    client_id = current_user.cliente_id
    return await movimiento_service.create_movimiento_con_detalles_servicio(
        client_id=client_id,
        data=data,
    )


@router.put(
    "/{movimiento_id}/con-detalle",
    response_model=MovimientoConDetalleRead,
    summary="Actualizar movimiento con reemplazo opcional de líneas",
)
async def actualizar_movimiento_con_detalles(
    movimiento_id: UUID,
    data: MovimientoConDetalleUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """
    Actualiza un movimiento en estado 'borrador'.
    Si se incluye 'detalles', reemplaza todas las líneas existentes (replace-all).
    Si no se incluye 'detalles', solo actualiza los campos de la cabecera.
    """
    client_id = current_user.cliente_id
    try:
        return await movimiento_service.update_movimiento_con_detalles_servicio(
            client_id=client_id,
            movimiento_id=movimiento_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
