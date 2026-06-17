# app/modules/inv/presentation/endpoints_almacenes.py
"""Endpoints INV - Almacenes. client_id desde sesión efectiva (inv_deps, patrón ORG)."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional

from app.api.deps import get_current_active_user
from app.modules.inv.presentation.inv_deps import get_inv_session_client_id
from app.core.authorization.rbac import require_permission
from app.core.exceptions import NotFoundError, AuthorizationError
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.inv.presentation.schemas import AlmacenCreate, AlmacenUpdate, AlmacenRead
from app.modules.inv.application.services import almacen_service

router = APIRouter()

MODULE_CODE = "inv"
RESOURCE_CODE = "almacen"


@router.get("", response_model=list[AlmacenRead], summary="Listar almacenes")
async def listar_almacenes(
    sucursal_id: Optional[UUID] = Query(None, description="Filtrar por sucursal"),
    solo_activos: bool = Query(True, description="Solo almacenes activos"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Lista almacenes de la empresa activa en sesión."""
    return await almacen_service.list_almacenes_servicio(
        client_id=client_id,
        sucursal_id=sucursal_id,
        solo_activos=solo_activos,
    )


@router.get("/{almacen_id}", response_model=AlmacenRead, summary="Detalle almacén")
async def detalle_almacen(
    almacen_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Detalle de un almacén de la empresa activa."""
    try:
        return await almacen_service.get_almacen_servicio(
            client_id=client_id,
            almacen_id=almacen_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=AlmacenRead, status_code=status.HTTP_201_CREATED, summary="Crear almacén")
async def crear_almacen(
    data: AlmacenCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Crea un almacén. empresa_id del body debe coincidir con la sesión."""
    try:
        return await almacen_service.create_almacen_servicio(client_id=client_id, data=data)
    except AuthorizationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.put("/{almacen_id}", response_model=AlmacenRead, summary="Actualizar almacén")
async def actualizar_almacen(
    almacen_id: UUID,
    data: AlmacenUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Actualiza un almacén de la empresa activa."""
    try:
        return await almacen_service.update_almacen_servicio(
            client_id=client_id,
            almacen_id=almacen_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.delete(
    "/{almacen_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar (baja lógica) almacén",
)
async def eliminar_almacen(
    almacen_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.eliminar")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Marca un almacén como inactivo en la empresa activa."""
    try:
        await almacen_service.update_almacen_servicio(
            client_id=client_id,
            almacen_id=almacen_id,
            data=AlmacenUpdate(es_activo=False),
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "/{almacen_id}/reactivar",
    response_model=AlmacenRead,
    summary="Reactivar almacén",
)
async def reactivar_almacen(
    almacen_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Reactiva un almacén de la empresa activa."""
    try:
        return await almacen_service.update_almacen_servicio(
            client_id=client_id,
            almacen_id=almacen_id,
            data=AlmacenUpdate(es_activo=True),
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
