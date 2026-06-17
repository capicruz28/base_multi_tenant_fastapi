# app/modules/inv/presentation/endpoints_inventario_fisico.py
"""Endpoints INV - Inventario Físico. client_id desde sesión efectiva (inv_deps, patrón ORG)."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional
from datetime import date

from app.api.deps import get_current_active_user
from app.modules.inv.presentation.inv_deps import get_inv_session_client_id
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
from app.core.exceptions import NotFoundError, AuthorizationError

router = APIRouter()

MODULE_CODE = "inv"
RESOURCE_CODE = "inventario_fisico"


@router.get("", response_model=list[InventarioFisicoRead], summary="Listar inventarios físicos")
async def listar_inventarios_fisicos(
    almacen_id: Optional[UUID] = Query(None, description="Filtrar por almacén"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    fecha_desde: Optional[date] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Lista inventarios físicos de la empresa activa en sesión."""
    try:
        return await inventario_fisico_service.list_inventarios_fisicos_servicio(
            client_id=client_id,
            almacen_id=almacen_id,
            estado=estado,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )
    except AuthorizationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/{inventario_fisico_id}", response_model=InventarioFisicoRead, summary="Detalle inventario físico")
async def detalle_inventario_fisico(
    inventario_fisico_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Detalle de un inventario físico de la empresa activa en sesión."""
    try:
        return await inventario_fisico_service.get_inventario_fisico_servicio(
            client_id=client_id,
            inventario_fisico_id=inventario_fisico_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except AuthorizationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=InventarioFisicoRead, status_code=status.HTTP_201_CREATED, summary="Crear inventario físico")
async def crear_inventario_fisico(
    data: InventarioFisicoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Crea un inventario físico. empresa_id debe coincidir con la sesión."""
    try:
        return await inventario_fisico_service.create_inventario_fisico_servicio(
            client_id=client_id, data=data
        )
    except AuthorizationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.put("/{inventario_fisico_id}", response_model=InventarioFisicoRead, summary="Actualizar inventario físico")
async def actualizar_inventario_fisico(
    inventario_fisico_id: UUID,
    data: InventarioFisicoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Actualiza un inventario físico de la empresa activa en sesión."""
    try:
        return await inventario_fisico_service.update_inventario_fisico_servicio(
            client_id=client_id,
            inventario_fisico_id=inventario_fisico_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except AuthorizationError as e:
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
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Anula un inventario físico de la empresa activa en sesión."""
    try:
        return await inventario_fisico_service.anular_inventario_fisico_servicio(
            client_id=client_id,
            inventario_fisico_id=inventario_fisico_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except AuthorizationError as e:
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
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Finaliza el conteo de un inventario físico de la empresa activa en sesión."""
    try:
        return await inventario_fisico_service.finalizar_inventario_fisico_servicio(
            client_id=client_id,
            inventario_fisico_id=inventario_fisico_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except AuthorizationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get(
    "/{inventario_fisico_id}/con-detalle",
    response_model=InventarioFisicoConDetalleRead,
    summary="Detalle de inventario físico con líneas de conteo embebidas",
)
async def detalle_inventario_fisico_con_detalles(
    inventario_fisico_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Retorna cabecera + detalles de la empresa activa en sesión."""
    try:
        return await inventario_fisico_service.get_inventario_fisico_con_detalles_servicio(
            client_id=client_id,
            inventario_fisico_id=inventario_fisico_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except AuthorizationError as e:
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
    client_id: UUID = Depends(get_inv_session_client_id),
):
    try:
        return await inventario_fisico_service.create_inventario_fisico_con_detalles_servicio(
            client_id=client_id,
            data=data,
        )
    except AuthorizationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


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
    client_id: UUID = Depends(get_inv_session_client_id),
):
    try:
        return await inventario_fisico_service.update_inventario_fisico_con_detalles_servicio(
            client_id=client_id,
            inventario_fisico_id=inventario_fisico_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except AuthorizationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
