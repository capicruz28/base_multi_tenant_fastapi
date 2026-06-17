# app/modules/inv/presentation/endpoints_categorias.py
"""Endpoints INV - Categorías. client_id desde sesión efectiva (inv_deps, patrón ORG)."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional, Union

from app.api.deps import get_current_active_user
from app.modules.inv.presentation.inv_deps import get_inv_session_client_id
from app.core.authorization.rbac import require_permission
from app.core.exceptions import NotFoundError, AuthorizationError
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.shared.pagination import erp_pagination_params, erp_sort_params, ErpPaginationParams, ErpSortParams
from app.modules.inv.presentation.schemas import (
    CategoriaCreate,
    CategoriaUpdate,
    CategoriaRead,
    PaginatedCategoriaResponse,
)
from app.modules.inv.application.services import categoria_service

router = APIRouter()

MODULE_CODE = "inv"
RESOURCE_CODE = "categoria"


@router.get(
    "",
    response_model=Union[list[CategoriaRead], PaginatedCategoriaResponse],
    summary="Listar categorías",
)
async def listar_categorias(
    solo_activos: bool = Query(True, description="Solo categorías activas"),
    buscar: Optional[str] = Query(None, description="Búsqueda por nombre o código"),
    pagination: ErpPaginationParams = Depends(erp_pagination_params),
    sort: ErpSortParams = Depends(erp_sort_params),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Lista categorías de la empresa activa en sesión."""
    return await categoria_service.list_categorias_servicio(
        client_id=client_id,
        solo_activos=solo_activos,
        buscar=buscar,
        pagination=pagination,
        sort=sort,
    )


@router.get("/{categoria_id}", response_model=CategoriaRead, summary="Detalle categoría")
async def detalle_categoria(
    categoria_id: UUID,
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Detalle de una categoría de la empresa activa."""
    try:
        return await categoria_service.get_categoria_servicio(
            client_id=client_id,
            categoria_id=categoria_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=CategoriaRead, status_code=status.HTTP_201_CREATED, summary="Crear categoría")
async def crear_categoria(
    data: CategoriaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Crea una categoría. empresa_id del body debe coincidir con la sesión."""
    try:
        return await categoria_service.create_categoria_servicio(
            client_id=client_id,
            data=data,
            usuario_id=current_user.usuario_id,
        )
    except AuthorizationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.put("/{categoria_id}", response_model=CategoriaRead, summary="Actualizar categoría")
async def actualizar_categoria(
    categoria_id: UUID,
    data: CategoriaUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Actualiza una categoría de la empresa activa."""
    try:
        return await categoria_service.update_categoria_servicio(
            client_id=client_id,
            categoria_id=categoria_id,
            data=data,
            usuario_id=current_user.usuario_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.delete(
    "/{categoria_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar (baja lógica) categoría",
)
async def eliminar_categoria(
    categoria_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.eliminar")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Marca una categoría como inactiva (es_activo = 0) en la empresa activa."""
    try:
        await categoria_service.update_categoria_servicio(
            client_id=client_id,
            categoria_id=categoria_id,
            data=CategoriaUpdate(es_activo=False),
            usuario_id=current_user.usuario_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "/{categoria_id}/reactivar",
    response_model=CategoriaRead,
    summary="Reactivar categoría",
)
async def reactivar_categoria(
    categoria_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Reactiva una categoría de la empresa activa."""
    try:
        return await categoria_service.update_categoria_servicio(
            client_id=client_id,
            categoria_id=categoria_id,
            data=CategoriaUpdate(es_activo=True),
            usuario_id=current_user.usuario_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
