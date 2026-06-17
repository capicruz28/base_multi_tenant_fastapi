# app/modules/inv/presentation/endpoints_tipos_movimiento.py
"""Endpoints INV - Tipos de Movimiento. client_id desde sesión efectiva (inv_deps, patrón ORG)."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID

from app.api.deps import get_current_active_user
from app.modules.inv.presentation.inv_deps import get_inv_session_client_id
from app.core.authorization.rbac import require_permission
from app.core.exceptions import NotFoundError, AuthorizationError
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.inv.presentation.schemas import TipoMovimientoCreate, TipoMovimientoUpdate, TipoMovimientoRead
from app.modules.inv.application.services import tipo_movimiento_service

router = APIRouter()

MODULE_CODE = "inv"
RESOURCE_CODE = "tipo_movimiento"


@router.get("", response_model=list[TipoMovimientoRead], summary="Listar tipos de movimiento")
async def listar_tipos_movimiento(
    solo_activos: bool = Query(True, description="Solo tipos activos"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Lista tipos de movimiento de la empresa activa en sesión."""
    return await tipo_movimiento_service.list_tipos_movimiento_servicio(
        client_id=client_id,
        solo_activos=solo_activos,
    )


@router.get("/{tipo_movimiento_id}", response_model=TipoMovimientoRead, summary="Detalle tipo de movimiento")
async def detalle_tipo_movimiento(
    tipo_movimiento_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Detalle de un tipo de movimiento de la empresa activa."""
    try:
        return await tipo_movimiento_service.get_tipo_movimiento_servicio(
            client_id=client_id,
            tipo_movimiento_id=tipo_movimiento_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=TipoMovimientoRead, status_code=status.HTTP_201_CREATED, summary="Crear tipo de movimiento")
async def crear_tipo_movimiento(
    data: TipoMovimientoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Crea un tipo de movimiento. empresa_id del body debe coincidir con la sesión."""
    try:
        return await tipo_movimiento_service.create_tipo_movimiento_servicio(client_id=client_id, data=data)
    except AuthorizationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.put("/{tipo_movimiento_id}", response_model=TipoMovimientoRead, summary="Actualizar tipo de movimiento")
async def actualizar_tipo_movimiento(
    tipo_movimiento_id: UUID,
    data: TipoMovimientoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Actualiza un tipo de movimiento de la empresa activa."""
    try:
        return await tipo_movimiento_service.update_tipo_movimiento_servicio(
            client_id=client_id,
            tipo_movimiento_id=tipo_movimiento_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.delete(
    "/{tipo_movimiento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar (baja lógica) tipo de movimiento",
)
async def eliminar_tipo_movimiento(
    tipo_movimiento_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.eliminar")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Marca un tipo de movimiento como inactivo en la empresa activa."""
    try:
        await tipo_movimiento_service.update_tipo_movimiento_servicio(
            client_id=client_id,
            tipo_movimiento_id=tipo_movimiento_id,
            data=TipoMovimientoUpdate(es_activo=False),
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "/{tipo_movimiento_id}/reactivar",
    response_model=TipoMovimientoRead,
    summary="Reactivar tipo de movimiento",
)
async def reactivar_tipo_movimiento(
    tipo_movimiento_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Reactiva un tipo de movimiento de la empresa activa."""
    try:
        return await tipo_movimiento_service.update_tipo_movimiento_servicio(
            client_id=client_id,
            tipo_movimiento_id=tipo_movimiento_id,
            data=TipoMovimientoUpdate(es_activo=True),
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
