# app/modules/inv/presentation/endpoints_inventario_fisico.py
"""Endpoints INV - Inventario Físico. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional
from datetime import date

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.inv.presentation.schemas import (
    InventarioFisicoCreate,
    InventarioFisicoUpdate,
    InventarioFisicoRead,
    InventarioFisicoConDetalleCreate,
    InventarioFisicoConDetalleUpdate,
    InventarioFisicoConDetalleRead,
)
from app.modules.inv.application.services import inventario_fisico_service
from app.core.exceptions import NotFoundError

router = APIRouter()

MODULE_CODE = "inv"
RESOURCE_CODE = "inventario_fisico"


@router.get("", response_model=list[InventarioFisicoRead], summary="Listar inventarios físicos")
async def listar_inventarios_fisicos(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    almacen_id: Optional[UUID] = Query(None, description="Filtrar por almacén"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    fecha_desde: Optional[date] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista inventarios físicos del tenant. Filtro por cliente_id del token."""
    client_id = current_user.cliente_id
    return await inventario_fisico_service.list_inventarios_fisicos_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        almacen_id=almacen_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )


@router.get("/{inventario_fisico_id}", response_model=InventarioFisicoRead, summary="Detalle inventario físico")
async def detalle_inventario_fisico(
    inventario_fisico_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Detalle de un inventario físico. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await inventario_fisico_service.get_inventario_fisico_servicio(
            client_id=client_id,
            inventario_fisico_id=inventario_fisico_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=InventarioFisicoRead, status_code=status.HTTP_201_CREATED, summary="Crear inventario físico")
async def crear_inventario_fisico(
    data: InventarioFisicoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Crea un inventario físico. cliente_id se asigna desde el contexto (tenant), no desde el body."""
    client_id = current_user.cliente_id
    return await inventario_fisico_service.create_inventario_fisico_servicio(client_id=client_id, data=data)


@router.put("/{inventario_fisico_id}", response_model=InventarioFisicoRead, summary="Actualizar inventario físico")
async def actualizar_inventario_fisico(
    inventario_fisico_id: UUID,
    data: InventarioFisicoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza un inventario físico. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await inventario_fisico_service.update_inventario_fisico_servicio(
            client_id=client_id,
            inventario_fisico_id=inventario_fisico_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "/{inventario_fisico_id}/anular",
    response_model=InventarioFisicoRead,
    summary="Anular inventario físico",
)
async def anular_inventario_fisico(
    inventario_fisico_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.anular")),
):
    """Anula un inventario físico dentro del tenant (cambia estado a 'anulado')."""
    client_id = current_user.cliente_id
    try:
        return await inventario_fisico_service.anular_inventario_fisico_servicio(
            client_id=client_id,
            inventario_fisico_id=inventario_fisico_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "/{inventario_fisico_id}/finalizar",
    response_model=InventarioFisicoRead,
    summary="Finalizar conteo de inventario físico",
)
async def finalizar_inventario_fisico(
    inventario_fisico_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.finalizar")),
):
    """
    Cierra el conteo de un inventario físico (estado 'en_proceso' → 'finalizado').
    Una vez finalizado, puede ser aprobado para generar el ajuste de stock.
    """
    client_id = current_user.cliente_id
    try:
        return await inventario_fisico_service.finalizar_inventario_fisico_servicio(
            client_id=client_id,
            inventario_fisico_id=inventario_fisico_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


# ============================================================================
# ENDPOINTS CABECERA + DETALLE EMBEBIDO
# ============================================================================

@router.get(
    "/{inventario_fisico_id}/con-detalle",
    response_model=InventarioFisicoConDetalleRead,
    summary="Detalle de inventario físico con líneas de conteo embebidas",
)
async def detalle_inventario_fisico_con_detalles(
    inventario_fisico_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Retorna la cabecera del inventario físico con todas sus líneas de conteo embebidas."""
    client_id = current_user.cliente_id
    try:
        return await inventario_fisico_service.get_inventario_fisico_con_detalles_servicio(
            client_id=client_id,
            inventario_fisico_id=inventario_fisico_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "/con-detalle",
    response_model=InventarioFisicoConDetalleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear inventario físico con líneas de conteo embebidas (recomendado)",
)
async def crear_inventario_fisico_con_detalles(
    data: InventarioFisicoConDetalleCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """
    Crea un inventario físico con sus líneas de conteo en una sola transacción atómica.
    Las líneas son opcionales al crear y pueden añadirse/reemplazarse en PUT posterior.
    """
    client_id = current_user.cliente_id
    return await inventario_fisico_service.create_inventario_fisico_con_detalles_servicio(
        client_id=client_id,
        data=data,
    )


@router.put(
    "/{inventario_fisico_id}/con-detalle",
    response_model=InventarioFisicoConDetalleRead,
    summary="Actualizar inventario físico con reemplazo opcional de líneas de conteo",
)
async def actualizar_inventario_fisico_con_detalles(
    inventario_fisico_id: UUID,
    data: InventarioFisicoConDetalleUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """
    Actualiza un inventario físico (estados distintos a 'ajustado' y 'anulado').
    Si se incluye 'detalles', reemplaza todas las líneas de conteo existentes (replace-all).
    Si no se incluye 'detalles', solo actualiza los campos de la cabecera.
    """
    client_id = current_user.cliente_id
    try:
        return await inventario_fisico_service.update_inventario_fisico_con_detalles_servicio(
            client_id=client_id,
            inventario_fisico_id=inventario_fisico_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
