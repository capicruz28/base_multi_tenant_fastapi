# app/modules/inv/presentation/endpoints_unidades_medida.py
"""Endpoints INV - Unidades de Medida. client_id desde sesión efectiva (inv_deps, patrón ORG)."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID

from app.api.deps import get_current_active_user
from app.modules.inv.presentation.inv_deps import get_inv_session_client_id
from app.core.authorization.rbac import require_permission
from app.core.exceptions import NotFoundError, AuthorizationError
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.inv.presentation.schemas import UnidadMedidaCreate, UnidadMedidaUpdate, UnidadMedidaRead
from app.modules.inv.application.services import unidad_medida_service

router = APIRouter()

MODULE_CODE = "inv"
RESOURCE_CODE = "unidad_medida"


@router.get("", response_model=list[UnidadMedidaRead], summary="Listar unidades de medida")
async def listar_unidades_medida(
    solo_activos: bool = Query(True, description="Solo unidades activas"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Lista unidades de medida de la empresa activa en sesión."""
    return await unidad_medida_service.list_unidades_medida_servicio(
        client_id=client_id,
        solo_activos=solo_activos,
    )


@router.get("/{unidad_medida_id}", response_model=UnidadMedidaRead, summary="Detalle unidad de medida")
async def detalle_unidad_medida(
    unidad_medida_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Detalle de una unidad de medida de la empresa activa."""
    try:
        return await unidad_medida_service.get_unidad_medida_servicio(
            client_id=client_id,
            unidad_medida_id=unidad_medida_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=UnidadMedidaRead, status_code=status.HTTP_201_CREATED, summary="Crear unidad de medida")
async def crear_unidad_medida(
    data: UnidadMedidaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Crea una unidad de medida. empresa_id del body debe coincidir con la sesión."""
    try:
        return await unidad_medida_service.create_unidad_medida_servicio(client_id=client_id, data=data)
    except AuthorizationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.put("/{unidad_medida_id}", response_model=UnidadMedidaRead, summary="Actualizar unidad de medida")
async def actualizar_unidad_medida(
    unidad_medida_id: UUID,
    data: UnidadMedidaUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Actualiza una unidad de medida de la empresa activa."""
    try:
        return await unidad_medida_service.update_unidad_medida_servicio(
            client_id=client_id,
            unidad_medida_id=unidad_medida_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.delete(
    "/{unidad_medida_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar (baja lógica) unidad de medida",
)
async def eliminar_unidad_medida(
    unidad_medida_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.eliminar")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Marca una unidad de medida como inactiva en la empresa activa."""
    try:
        await unidad_medida_service.update_unidad_medida_servicio(
            client_id=client_id,
            unidad_medida_id=unidad_medida_id,
            data=UnidadMedidaUpdate(es_activo=False),
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "/{unidad_medida_id}/reactivar",
    response_model=UnidadMedidaRead,
    summary="Reactivar unidad de medida",
)
async def reactivar_unidad_medida(
    unidad_medida_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Reactiva una unidad de medida de la empresa activa."""
    try:
        return await unidad_medida_service.update_unidad_medida_servicio(
            client_id=client_id,
            unidad_medida_id=unidad_medida_id,
            data=UnidadMedidaUpdate(es_activo=True),
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
