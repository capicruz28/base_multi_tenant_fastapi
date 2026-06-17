# app/modules/org/presentation/endpoints_parametros.py
"""Endpoints ORG - Parámetros (HYBRID). Lectura contextual ERP + escritura por ámbito (Etapa C2)."""
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from uuid import UUID
from typing import Optional, Union

from app.api.deps import get_current_user_data
from app.core.authorization.rbac import require_permission
from app.core.exceptions import AuthorizationError, ConflictError, CustomException, NotFoundError
from app.shared.pagination import erp_pagination_params, erp_sort_params, ErpPaginationParams, ErpSortParams
from app.modules.org.presentation.org_deps import (
    get_org_session_client_id,
    reject_legacy_empresa_query,
    user_can_manage_global_parametros,
)
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.org.presentation.schemas import (
    ParametroCreate,
    ParametroUpdate,
    ParametroRead,
    PaginatedParametroResponse,
)
from app.modules.org.application.services import parametro_service

router = APIRouter()


@router.get(
    "",
    response_model=Union[list[ParametroRead], PaginatedParametroResponse],
    summary="Listar parámetros",
)
async def listar_parametros(
    modulo_codigo: Optional[str] = Query(None),
    solo_activos: bool = True,
    buscar: Optional[str] = Query(
        None,
        description="Búsqueda por módulo, código o nombre de parámetro",
    ),
    pagination: ErpPaginationParams = Depends(erp_pagination_params),
    sort: ErpSortParams = Depends(erp_sort_params),
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.parametro.leer")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    """
    Lista efectiva para la empresa activa: globales tenant + overrides con precedencia.
    """
    return await parametro_service.list_parametros_servicio(
        client_id=client_id,
        modulo_codigo=modulo_codigo,
        solo_activos=solo_activos,
        buscar=buscar,
        pagination=pagination,
        sort=sort,
    )


@router.post(
    "/{parametro_id}/reactivar",
    response_model=ParametroRead,
    summary="Reactivar parámetro",
)
async def reactivar_parametro(
    parametro_id: UUID,
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.parametro.actualizar")),
    client_id: UUID = Depends(get_org_session_client_id),
    payload: dict = Depends(get_current_user_data),
):
    try:
        return await parametro_service.reactivar_parametro_servicio(
            client_id=client_id,
            parametro_id=parametro_id,
            can_manage_global=user_can_manage_global_parametros(current_user, payload),
        )
    except (NotFoundError, AuthorizationError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.get("/{parametro_id}", response_model=ParametroRead, summary="Detalle parámetro")
async def detalle_parametro(
    parametro_id: UUID,
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.parametro.leer")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    try:
        return await parametro_service.get_parametro_servicio(
            client_id=client_id,
            parametro_id=parametro_id,
        )
    except (NotFoundError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.post("", response_model=ParametroRead, status_code=201, summary="Crear parámetro")
async def crear_parametro(
    data: ParametroCreate,
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.parametro.crear")),
    client_id: UUID = Depends(get_org_session_client_id),
    payload: dict = Depends(get_current_user_data),
):
    """
    Global (empresa_id null): tenant_admin/platform.
    Empresa: empresa_id del body debe coincidir con la sesión.
    """
    try:
        return await parametro_service.create_parametro_servicio(
            client_id=client_id,
            data=data,
            can_manage_global=user_can_manage_global_parametros(current_user, payload),
        )
    except (AuthorizationError, ConflictError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.put("/{parametro_id}", response_model=ParametroRead, summary="Actualizar parámetro")
async def actualizar_parametro(
    parametro_id: UUID,
    data: ParametroUpdate = Body(...),
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.parametro.actualizar")),
    client_id: UUID = Depends(get_org_session_client_id),
    payload: dict = Depends(get_current_user_data),
):
    try:
        return await parametro_service.update_parametro_servicio(
            client_id=client_id,
            parametro_id=parametro_id,
            data=data,
            can_manage_global=user_can_manage_global_parametros(current_user, payload),
        )
    except (NotFoundError, AuthorizationError, ConflictError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.delete(
    "/{parametro_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar (baja lógica) parámetro",
)
async def eliminar_parametro(
    parametro_id: UUID,
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.parametro.eliminar")),
    client_id: UUID = Depends(get_org_session_client_id),
    payload: dict = Depends(get_current_user_data),
):
    try:
        await parametro_service.delete_parametro_servicio(
            client_id=client_id,
            parametro_id=parametro_id,
            can_manage_global=user_can_manage_global_parametros(current_user, payload),
        )
    except (NotFoundError, AuthorizationError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
